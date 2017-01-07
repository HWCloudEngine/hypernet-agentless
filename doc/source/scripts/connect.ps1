$UserData = Invoke-RestMethod 'http://169.254.169.254/latest/user-data'
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
$need-restart = $false

While ($mac -ne "") {
    $hsservers = $hsservers -split ","
    $openvpn_bin_dir = "C:\Program Files\OpenVPN\bin"
    $openvpn_conf_dir = "C:\Program Files\OpenVPN\config"
    $openvpn_file_conf = "c-hs.ovpn"
    
    # TODO: create the tap if not exist
    $ind = $i + 2
    $vpn_eth = "Ethernet " + $ind
    cd $openvpn_conf_dir
    
    "client" | Out-File -FilePath $openvpn_file_conf -enc UTF8
    "dev tap" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "dev-node ""$vpn_eth""" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    "proto tcp" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
    foreach ($hsserver in $hsservers) {
        "remote $hsserver.trim() 1194" | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
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
    
    $cur_mac = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\0012").MAC
    echo "mac: $mac"
    echo "cur_mac: $cur_mac"
    If ($cur_mac -ne $mac){
       netsh interface set interface "Ethernet 2" disable
       echo "Not same mac"
       reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\0012" /v MAC /f
       reg add    "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\0012" /v MAC /d $mac
       netsh interface set interface "Ethernet 2" enable
       $need-restart = $true
    }
    
    #netsh interface ipv4 set address name=Ethernet static $ip $netmask
    
    netsh interface ipv4 set address name=Ethernet source=dhcp
    
    cd $openvpn_bin_dir
    openvpn-gui.exe --connect c-hs.ovpn --config_dir $openvpn_conf_dir

    $i = $i + 1
	$hsservers = $userdata."hsservers$i"
	$mac = $userdata."mac$i"
}
if ($need-restart) {
    Restart-Computer
}