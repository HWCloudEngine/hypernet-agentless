 $log_file = "C:\hybrid\connect.log"

Function LogMessage ([string]$message) {
    $d = Get-Date
    echo "$d --- $message" | Out-File -FilePath $log_file -Append -enc UTF8
}


Function WriteLine ([string]$message) {
    $message | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8 2>>$log_file
}

LogMessage "---------------------  Begin ---------------------"

Stop-Process -processname "openvpn-gui" 2>>$log_file
net stop OpenVpnService 2>>$log_file
net stop OpenVPNServiceInteractive 2>>$log_file
LogMessage ""

LogMessage "OpenVPN service stopped"

# user data format:
# hsservers0 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
# mac0 = 00:00:00:00:00:00
# port0 = XXXX
# hsservers1 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
# mac1 = 00:00:00:00:00:00
# port1 = XXXX

$UserData = Invoke-RestMethod 'http://169.254.169.254/1.0/user-data' 2>>$log_file
LogMessage "user data: $UserData"

$userdata = ConvertFrom-StringData -StringData $UserData

$i = 0
$hsservers = $userdata."hsservers$i"
$mac = $userdata."mac$i"
$port = $userdata."port$i"
$need_restart = $false

$n_eth = "Ethernet"
LogMessage "n_eth : $n_eth"

$tap_bin_dir = "C:\Program Files\Tap-Windows\bin"
$openvpn_conf_dir = "C:\Program Files\OpenVPN\config"
$openvpn_log_dir = "C:\Program Files\OpenVPN\log"


del $openvpn_conf_dir"\c-hs-*.ovpn" 2>>$log_file
del $openvpn_log_dir"\c-hs-*.log" 2>>$log_file


While ("$mac" -ne "") {

    LogMessage "Port: $i"
    LogMessage "mac: '$mac'"
    LogMessage "hsservers: '$hsservers'"
    LogMessage "port: '$port'"

    $hsservers = $hsservers -split ","
    $openvpn_file_conf = "c-hs-" + $i + ".ovpn"
    
    $vpn_ind = $i + 2
    $vpn_eth = "Ethernet " + $vpn_ind

    LogMessage "vpn_eth: '$vpn_eth'"
    $vpn_nic_exist = openvpn --show-adapters | findstr /R /C:"$vpn_eth" 2>>$log_file
    if ("$vpn_nic_exist" -eq "") {
        cd $tap_bin_dir
        .\tapinstall.exe install "C:\Program Files\TAP-Windows\driver\OemVista.inf" tap0901 2>>$log_file
    }
    cd $openvpn_conf_dir
    WriteLine "client"
    WriteLine "dev tap"
    WriteLine "dev-node ""$vpn_eth"""
    WriteLine "proto udp"
    foreach ($hsserver in $hsservers) {
        $hsserver = $hsserver.trim()
        WriteLine "remote $hsserver $port"
    }
    WriteLine "resolv-retry infinite"
    WriteLine "auth none"
    WriteLine "cipher none"
    WriteLine "nobind"
    WriteLine "persist-key"
    WriteLine "persist-tun"
    WriteLine "ca ca.crt"
    WriteLine "cert client.crt"
    WriteLine "key client.key"
    WriteLine "verb 3"
    if ("$i" -eq "0") {
        WriteLine "redirect-gateway local"
    }

    # search the reg key
    $d_id_0 = "ROOT\NET\000" + $i
    echo "d_id_0: '$d_id_0'"
    for ($a = 10; $a -le 30; $a++){
        $reg_key = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\00" + $a
        LogMessage "regkey: '$reg_key'" 
        $d_id = (Get-ItemProperty -Path "$reg_key").DeviceInstanceID
        if ($d_id -eq $d_id_0) {
            Break
        }
    }
    if ($d_id -eq $d_id_0) {
        $cur_mac = (Get-ItemProperty -Path "$reg_key").MAC
        echo "mac: '$mac'"
        echo "cur_mac: '$cur_mac'"
        echo "reg_key: '$reg_key'"
        If ($cur_mac -ne $mac){
           netsh interface set interface "$vpn_eth" disable 2>>$log_file
           LogMessage "Not same mac: Need restart"
           Remove-ItemProperty -Path $reg_key -Name "MAC" 2>>$log_file
           New-ItemProperty -Path $reg_key -Name "MAC" -Value "$mac" 2>>$log_file
           $need_restart = $true
        }
    }

    netsh interface set interface "$vpn_eth" enable
    
    $i = $i + 1
    $hsservers = $userdata."hsservers$i"
    $mac = $userdata."mac$i"
    $port = $userdata."port$i"
}

if ($need_restart) {
    Restart-Computer
}

# restart openvpn service
net start OpenVpnService 2>>$log_file
LogMessage ""

$init_ok = findstr /R /C:"Initialization Sequence Completed" "C:\Program Files\OpenVPN\log\c-hs-0.log"
while ($init_ok -eq ""){
    LogMessage "waiting for connection..."
    Start-Sleep -s 2
    $init_ok = findstr /R /C:"Initialization Sequence Completed" "C:\Program Files\OpenVPN\log\c-hs-0.log"
}
LogMessage "!!!connected!!!!"
LogMessage "--------------------- End ---------------------"