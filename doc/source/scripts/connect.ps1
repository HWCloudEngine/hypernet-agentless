Stop-Process -processname "openvpn-gui"
net stop OpenVpnService
net stop OpenVPNServiceInteractive

netsh interface set interface "Ethernet"   disable
netsh interface set interface "Ethernet 2" disable
netsh interface set interface "Ethernet 3" disable
netsh interface set interface "Ethernet 4" disable
netsh interface set interface "Ethernet 5" disable
netsh interface ipv4 set address name=Ethernet source=dhcp
netsh interface set interface "Ethernet" enable

Start-Sleep -s 5

$UserData = Invoke-RestMethod 'http://169.254.169.254/1.0/user-data'
echo "user-data: $UserData"

$userdata = ConvertFrom-StringData -StringData $UserData
# format:
# hsservers0 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
# mac0 = 00:00:00:00:00:00
# hsservers1 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
# mac1 = 00:00:00:00:00:00

$i = 0
$hsservers = $userdata."hsservers$i"
$mac = $userdata."mac$i"
$port = $userdata."port$i"
$need_restart = $false

While ("$mac" -ne "") {

    echo "mac: '$mac'"
    echo "hsservers: '$hsservers'"
    $hsservers = $hsservers -split ","
    $openvpn_bin_dir = "C:\Program Files\OpenVPN\bin"
    $openvpn_conf_dir = "C:\Program Files\OpenVPN\config"
    $openvpn_file_conf = "c-hs-" + $i + ".ovpn"
    
    if ($i -eq 0) {
        $n_eth = "Ethernet"
        $vpn_eth = "Ethernet 2"
    } else {
        $n_ind = 2 * $i + 1
        $n_eth = "Ethernet " + $n_ind
        $vpn_ind = 2 * $i + 2
        $vpn_eth = "Ethernet " + $vpn_ind
    }
    echo "n_eth: '$n_eth'"
    echo "vpn_eth: '$vpn_eth'"
    netsh interface ipv4 set address name="$n_eth" source=dhcp
    netsh interface set interface "$n_eth" enable

    cd $openvpn_conf_dir

    "client" | Out-File -FilePath $openvpn_file_conf -enc UTF8
    "dev tap" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "dev-node ""$vpn_eth""" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "proto udp" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    foreach ($hsserver in $hsservers) {
        $hsserver = $hsserver.trim()
        "remote $hsserver $port" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    }
    "resolv-retry infinite" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "auth none" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "cipher none" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "nobind" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "persist-key" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "persist-tun" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "ca ca.crt" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "cert client.crt" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "key client.key" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "verb 3" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    
    # serach the reg key
    $d_id_0 = "ROOT\NET\000" + $i
    echo "d_id_0: '$d_id_0'"
    for ($a = 10; $a -le 30; $a++){
        $reg_key = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\00" + $a
        echo "regkey: '$reg_key'" 
        $d_id = (Get-ItemProperty -Path "$reg_key").DeviceInstanceID
        if ($d_id -eq $d_id_0) {
            Break
        }
    }
    $cur_mac = (Get-ItemProperty -Path "$reg_key").MAC
    echo "mac: '$mac'"
    echo "cur_mac: '$cur_mac'"
    echo "reg_key: '$reg_key'"
    If ($cur_mac -ne $mac){
       netsh interface set interface "$vpn_eth" disable
       echo "Not same mac"
       Remove-ItemProperty -Path $reg_key -Name "MAC"
       New-ItemProperty -Path $reg_key -Name "MAC" -Value "$mac"
       netsh interface set interface "$vpn_eth" enable
       $need_restart = $true
    }

    $ip = netsh int ip show config name="$n_eth" | findstr /R /C:"IP Address"
    $ip = $ip.split(":")[1].trim()
    $netmask = netsh int ip show config name="$n_eth" | findstr /R /C:"Subnet"
    $netmask = $netmask.split(":")[1].trim().split(" ")[2].trim().split(")")[0].trim()
    echo "netmask: '$netmask'"
    netsh interface ipv4 set address name="$n_eth" static $ip $netmask
    netsh interface set interface "$n_eth" enable
    netsh interface set interface "$vpn_eth" enable
    
#    cd $openvpn_bin_dir
#    openvpn-gui.exe --connect c-hs.ovpn --config_dir $openvpn_conf_dir

    $i = $i + 1
    $hsservers = $userdata."hsservers$i"
    $mac = $userdata."mac$i"
    $port = $userdata."port$i"
}

if ($need_restart) {
    Restart-Computer
}

net start OpenVpnService

Start-Sleep -s 5

net stop OpenVpnService
net start OpenVpnService
