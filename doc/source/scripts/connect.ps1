###############################################################################
#                                                                             #
#   File name       connect.ps1                                               #
#                                                                             #
#   Description     Hyper interface service in PowerShell script              #
#                                                                             #
#   Notes                                                                     #
#                   connect service will set the hyper interface vpn          #
#                   connection to the hybrid cloud overlay hub (hyper switch).#
#                   Only once the vpn connection is established, the          #
#                   cloudinit will be kicked started. This way we make sure   #
#                   Service management arguments: -Start, -Stop, -Restart,    #
#                   -Status (unix style), -Setup, -Remove (win style)         #
#                                                                             #
#                   The actual start and stop operations are done when        #
#                   running as SYSTEM, under the control of the SCM (Service  #
#                   Control Manager).                                         #
#                                                                             #
#                   Service installation and usage: See the dynamic help      #
#                   section below, or run: help .\connect.ps1 -Detailed       #
#                                                                             #
#                                                                             #
###############################################################################
#Requires -version 2

<#
  .SYNOPSIS
    Hyper interface service in PowerShell script.

  .DESCRIPTION
    This script demonstrates how to write a Windows service in pure PowerShell.
    It dynamically generates a small connect.exe wrapper, that in turn
    invokes this PowerShell script again for its start and stop events.

  .PARAMETER Start
    Start the service.

  .PARAMETER Stop
    Stop the service.

  .PARAMETER Restart
    Stop then restart the service.

  .PARAMETER Status
    Get the current service status: Not installed / Stopped / Running

  .PARAMETER Setup
    Install the service.

  .PARAMETER Remove
    Uninstall the service.

  .PARAMETER Version
    Display this script version and exit.

  .EXAMPLE
    # Setup the service and run it for the first time
    C:\PS>.\connect.ps1 -Status
    Not installed
    C:\PS>.\connect.ps1 -Setup
    C:\PS># At this stage, a copy of connect.ps1 is present in the path
    C:\PS>connect -Status
    Stopped
    C:\PS>connect -Start
    C:\PS>connect -Status
    Running
    C:\PS># Load the log file in Notepad.exe for review
    C:\PS>notepad ${ENV:windir}\Logs\connect.log

  .EXAMPLE
    # Stop the service and uninstall it.
    C:\PS>connect -Stop
    C:\PS>connect -Status
    Stopped
    C:\PS>connect -Remove
    C:\PS># At this stage, no copy of connect.ps1 is present in the path anymore
    C:\PS>.\connect.ps1 -Status
    Not installed

#>

[CmdletBinding(DefaultParameterSetName='Status')]
Param(
  [Parameter(ParameterSetName='Start', Mandatory=$true)]
  [Switch]$Start,               # Start the service

  [Parameter(ParameterSetName='Stop', Mandatory=$true)]
  [Switch]$Stop,                # Stop the service

  [Parameter(ParameterSetName='Restart', Mandatory=$true)]
  [Switch]$Restart,             # Restart the service

  [Parameter(ParameterSetName='Status', Mandatory=$false)]
  [Switch]$Status = $($PSCmdlet.ParameterSetName -eq 'Status'), # Get the current service status

  [Parameter(ParameterSetName='Setup', Mandatory=$true)]
  [Switch]$Setup,               # Install the service

  [Parameter(ParameterSetName='Remove', Mandatory=$true)]
  [Switch]$Remove,              # Uninstall the service

  [Parameter(ParameterSetName='Version', Mandatory=$true)]
  [Switch]$Version              # Get this script version
)

$scriptVersion = "2017-13-08"

$ca_crt = @"
-----BEGIN CERTIFICATE-----
MIIE1jCCA76gAwIBAgIJANQ3qW6bgQkSMA0GCSqGSIb3DQEBCwUAMIGiMQswCQYD
VQQGEwJJTDELMAkGA1UECBMCSUwxFTATBgNVBAcTDEhvZCBIYXNoYXJvbjENMAsG
A1UEChMEVG9nYTEPMA0GA1UECxMGc2VydmVyMRAwDgYDVQQDEwdkZW1vdnBuMRQw
EgYDVQQpEwtoeXBlcnN3aXRjaDEnMCUGCSqGSIb3DQEJARYYbGlvbmVsLnplcmJp
YkBodWF3ZWkuY29tMB4XDTE3MDEwNDEzMzIwOVoXDTI3MDEwMjEzMzIwOVowgaIx
CzAJBgNVBAYTAklMMQswCQYDVQQIEwJJTDEVMBMGA1UEBxMMSG9kIEhhc2hhcm9u
MQ0wCwYDVQQKEwRUb2dhMQ8wDQYDVQQLEwZzZXJ2ZXIxEDAOBgNVBAMTB2RlbW92
cG4xFDASBgNVBCkTC2h5cGVyc3dpdGNoMScwJQYJKoZIhvcNAQkBFhhsaW9uZWwu
emVyYmliQGh1YXdlaS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
AQC5DD1ffCNWUXuyKzSvGGrN423EbNkIJmDMtESlii6ikPnaGHr7L70aMQVmaUJd
Q8Yddjg9ncc0VCI5GIBsfHVPf/Eqd3gkoilmTif1r7Cfqgnl251gN4V2GHj2bjU6
yh5rRaQUde5k/d1eIdms+e3lAZ61A/5nPd8XC0rjOlxZ4ADcq8SPDB0ZXGDF2Y2X
b8PmPL7CU1CCG/6UKA4deXI0WfgFZKKVBKqkL2u2Y/nLS/kE1xdBF1USRDuOhRK7
F2EhIEj7n4szFkpQNnLf+yCbqRyi3nvbsfebTZX3RNBqZJBEc5020/tQ8ioE2lj1
clo2HgFHh1dfG4DdHd30LXu5AgMBAAGjggELMIIBBzAdBgNVHQ4EFgQUgIr1zZzi
E/vIkKavwZG6VVwQfeswgdcGA1UdIwSBzzCBzIAUgIr1zZziE/vIkKavwZG6VVwQ
feuhgaikgaUwgaIxCzAJBgNVBAYTAklMMQswCQYDVQQIEwJJTDEVMBMGA1UEBxMM
SG9kIEhhc2hhcm9uMQ0wCwYDVQQKEwRUb2dhMQ8wDQYDVQQLEwZzZXJ2ZXIxEDAO
BgNVBAMTB2RlbW92cG4xFDASBgNVBCkTC2h5cGVyc3dpdGNoMScwJQYJKoZIhvcN
AQkBFhhsaW9uZWwuemVyYmliQGh1YXdlaS5jb22CCQDUN6lum4EJEjAMBgNVHRME
BTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQB9YN1QYCEZ3m3Oo45YTrY7v2LrwviA
A+3EztW6Emx9LnJgUdl24SCwTj3i1mvdfWxpo860pNUXuPQ7OwrDBWzPitqp8HJF
bkEp+fBIzefTlSkNRL8hZIcwTZb+uVFFmuJkWUjGv8vzxTvOmlYZN5wjcwtAXhcl
CpV9N/jpaLeng4x/uAc9fgvlx3rQHFKbN7h72I4c/sOmM6q/+lFOt12pJXdku4o3
aIy4FwupE6cL4l8lgs15f4E1gtYpXSqryMyxb486DyZxwPEnju0sSf8d8u27hKA0
11ct2PfvhFJjmlYypuC7D50pHhyYxL94kjMxDT1qaQm90HQxuDIwcx6O
-----END CERTIFICATE-----
"@

$client_crt = @"
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 2 (0x2)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=IL, ST=IL, L=Hod Hasharon, O=Toga, OU=server, CN=demovpn/name=hyperswitch/emailAddress=lionel.zerbib@huawei.com
        Validity
            Not Before: Jan  4 13:39:46 2017 GMT
            Not After : Jan  2 13:39:46 2027 GMT
        Subject: C=IL, ST=IL, L=Hod Hasharon, O=Toga, OU=server, CN=client/name=hyperswitch/emailAddress=lionel.zerbib@huawei.com
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:c8:1d:ad:fc:71:ad:62:32:0f:38:ed:39:1e:5c:
                    5f:32:a6:d0:96:ca:50:5a:52:26:8b:d5:3c:01:a8:
                    69:63:a2:8e:55:6c:cc:b5:95:71:60:34:27:a3:2d:
                    f7:1e:fd:13:c4:1f:46:1d:ca:81:5d:ff:be:c9:38:
                    69:a7:38:ee:8d:12:2d:fb:cd:79:d4:63:0c:0a:5f:
                    f6:d3:c1:7e:c0:09:8b:6c:a5:07:ca:0e:bb:b0:f3:
                    f2:c5:ac:21:4f:39:cd:77:eb:bd:44:e1:f1:d4:7b:
                    46:83:5f:ad:f7:e5:6d:70:7c:20:6e:71:e7:ca:68:
                    98:df:d6:8b:35:0a:88:24:bf:2f:5c:4f:66:bb:7d:
                    70:ab:87:59:74:15:47:b0:92:97:05:84:96:22:8f:
                    8c:ed:cb:d8:38:f6:6f:1d:6b:fd:d8:15:95:6a:d0:
                    01:29:4f:71:b3:cb:46:c2:09:da:a4:29:56:e1:72:
                    91:2c:b3:f6:c6:f4:c6:9f:1e:63:a0:df:8b:b6:68:
                    0b:9f:4b:c0:a5:29:ee:dc:da:fb:87:0e:37:b9:ee:
                    7e:41:c3:8d:2c:2c:5a:b8:c3:25:de:58:fe:a7:1b:
                    ea:e5:7a:43:ca:18:b8:74:e2:f6:f4:f5:2c:ef:63:
                    51:70:3f:09:ac:73:4d:6b:87:16:0a:e2:a9:7a:68:
                    8e:f3
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Basic Constraints: 
                CA:FALSE
            Netscape Comment: 
                Easy-RSA Generated Certificate
            X509v3 Subject Key Identifier: 
                9B:AE:72:C2:2F:69:99:99:F7:EE:1E:63:41:75:3E:71:7E:43:50:EE
            X509v3 Authority Key Identifier: 
                keyid:80:8A:F5:CD:9C:E2:13:FB:C8:90:A6:AF:C1:91:BA:55:5C:10:7D:EB
                DirName:/C=IL/ST=IL/L=Hod Hasharon/O=Toga/OU=server/CN=demovpn/name=hyperswitch/emailAddress=lionel.zerbib@huawei.com
                serial:D4:37:A9:6E:9B:81:09:12

            X509v3 Extended Key Usage: 
                TLS Web Client Authentication
            X509v3 Key Usage: 
                Digital Signature
    Signature Algorithm: sha256WithRSAEncryption
         9e:54:b4:d4:63:46:f7:61:af:1b:a2:42:df:db:a6:e9:59:4f:
         a2:82:81:ae:b9:75:d6:4d:5c:bd:a6:ab:01:7e:37:8f:56:b5:
         37:03:83:1a:a0:33:71:fe:53:78:8e:79:a4:c7:e8:4e:a8:7e:
         4e:30:b6:e1:eb:ce:56:1d:b7:d0:01:80:16:8b:31:17:42:fa:
         86:9b:5d:d3:9e:10:b0:22:62:78:a9:16:52:42:74:0c:3f:40:
         ae:65:4e:45:28:96:d0:ff:ff:84:c0:d5:79:93:31:6f:2d:96:
         1b:4c:ca:f1:94:fe:53:70:55:76:c8:70:0d:75:61:5f:96:28:
         10:37:ca:e0:ce:a9:68:a5:21:5e:97:82:2e:7d:bb:3e:56:ff:
         89:9f:8e:dd:76:62:2c:85:af:bb:04:0a:07:c2:a3:e7:47:7d:
         da:cb:3b:72:b6:0d:74:9c:be:e5:96:82:f1:2c:26:65:82:87:
         25:69:a7:50:9b:ce:c2:dc:98:f7:6a:eb:a8:d8:c8:56:94:94:
         95:99:fd:c1:a4:45:3a:f6:45:ed:6d:80:72:82:ae:af:e9:a8:
         b4:d7:75:0d:2e:60:1e:85:88:bb:91:db:eb:ea:d4:1f:5d:39:
         35:02:9c:a0:d3:03:80:42:de:66:cd:48:b8:73:06:0c:8d:96:
         08:9c:32:00
-----BEGIN CERTIFICATE-----
MIIFGzCCBAOgAwIBAgIBAjANBgkqhkiG9w0BAQsFADCBojELMAkGA1UEBhMCSUwx
CzAJBgNVBAgTAklMMRUwEwYDVQQHEwxIb2QgSGFzaGFyb24xDTALBgNVBAoTBFRv
Z2ExDzANBgNVBAsTBnNlcnZlcjEQMA4GA1UEAxMHZGVtb3ZwbjEUMBIGA1UEKRML
aHlwZXJzd2l0Y2gxJzAlBgkqhkiG9w0BCQEWGGxpb25lbC56ZXJiaWJAaHVhd2Vp
LmNvbTAeFw0xNzAxMDQxMzM5NDZaFw0yNzAxMDIxMzM5NDZaMIGhMQswCQYDVQQG
EwJJTDELMAkGA1UECBMCSUwxFTATBgNVBAcTDEhvZCBIYXNoYXJvbjENMAsGA1UE
ChMEVG9nYTEPMA0GA1UECxMGc2VydmVyMQ8wDQYDVQQDEwZjbGllbnQxFDASBgNV
BCkTC2h5cGVyc3dpdGNoMScwJQYJKoZIhvcNAQkBFhhsaW9uZWwuemVyYmliQGh1
YXdlaS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDIHa38ca1i
Mg847TkeXF8yptCWylBaUiaL1TwBqGljoo5VbMy1lXFgNCejLfce/RPEH0YdyoFd
/77JOGmnOO6NEi37zXnUYwwKX/bTwX7ACYtspQfKDruw8/LFrCFPOc13671E4fHU
e0aDX6335W1wfCBucefKaJjf1os1Cogkvy9cT2a7fXCrh1l0FUewkpcFhJYij4zt
y9g49m8da/3YFZVq0AEpT3Gzy0bCCdqkKVbhcpEss/bG9MafHmOg34u2aAufS8Cl
Ke7c2vuHDje57n5Bw40sLFq4wyXeWP6nG+rlekPKGLh04vb09SzvY1FwPwmsc01r
hxYK4ql6aI7zAgMBAAGjggFZMIIBVTAJBgNVHRMEAjAAMC0GCWCGSAGG+EIBDQQg
Fh5FYXN5LVJTQSBHZW5lcmF0ZWQgQ2VydGlmaWNhdGUwHQYDVR0OBBYEFJuucsIv
aZmZ9+4eY0F1PnF+Q1DuMIHXBgNVHSMEgc8wgcyAFICK9c2c4hP7yJCmr8GRulVc
EH3roYGopIGlMIGiMQswCQYDVQQGEwJJTDELMAkGA1UECBMCSUwxFTATBgNVBAcT
DEhvZCBIYXNoYXJvbjENMAsGA1UEChMEVG9nYTEPMA0GA1UECxMGc2VydmVyMRAw
DgYDVQQDEwdkZW1vdnBuMRQwEgYDVQQpEwtoeXBlcnN3aXRjaDEnMCUGCSqGSIb3
DQEJARYYbGlvbmVsLnplcmJpYkBodWF3ZWkuY29tggkA1DepbpuBCRIwEwYDVR0l
BAwwCgYIKwYBBQUHAwIwCwYDVR0PBAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQCe
VLTUY0b3Ya8bokLf26bpWU+igoGuuXXWTVy9pqsBfjePVrU3A4MaoDNx/lN4jnmk
x+hOqH5OMLbh685WHbfQAYAWizEXQvqGm13TnhCwImJ4qRZSQnQMP0CuZU5FKJbQ
//+EwNV5kzFvLZYbTMrxlP5TcFV2yHANdWFfligQN8rgzqlopSFel4Iufbs+Vv+J
n47ddmIsha+7BAoHwqPnR33ayztytg10nL7lloLxLCZlgoclaadQm87C3Jj3auuo
2MhWlJSVmf3BpEU69kXtbYBygq6v6ai013UNLmAehYi7kdvr6tQfXTk1Apyg0wOA
Qt5mzUi4cwYMjZYInDIA
-----END CERTIFICATE-----
"@

$client_key = @"
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDIHa38ca1iMg84
7TkeXF8yptCWylBaUiaL1TwBqGljoo5VbMy1lXFgNCejLfce/RPEH0YdyoFd/77J
OGmnOO6NEi37zXnUYwwKX/bTwX7ACYtspQfKDruw8/LFrCFPOc13671E4fHUe0aD
X6335W1wfCBucefKaJjf1os1Cogkvy9cT2a7fXCrh1l0FUewkpcFhJYij4zty9g4
9m8da/3YFZVq0AEpT3Gzy0bCCdqkKVbhcpEss/bG9MafHmOg34u2aAufS8ClKe7c
2vuHDje57n5Bw40sLFq4wyXeWP6nG+rlekPKGLh04vb09SzvY1FwPwmsc01rhxYK
4ql6aI7zAgMBAAECggEARVOC4uG+3zXYcDA+iXYWxMVlndeY3rF3CRpmH2zolcvK
4209vep3zIxE7xMNeX7TSi5LbCaripT+01bnwzbF7blOlN0qR5nIog98wv9VmdG0
q37ApA9Wlobso+5t27R6qgDRIPvle2b5lqme6zJgJ4fY9Gohks2JqIH61/U+FPxJ
5/s8cqf3jfSEaVY2nTma1KqgUiMy0bGigjz6IamTB3Pu8H6rQ2BKGuEcIijU3klW
pSHGf75J1XW3IuMVLKnpHnpW797U9BoVyvlYbCRvPHW479DgoNxNAU4ZC6/1tiPi
NEopkDoZ0nApT4riX83+AFzIpYobmyAbIYZ5YnCsAQKBgQDj82qbidkRXGn48cpL
Tk5J3Cd5jqwi7a21F9bVoy1qt9GMNGZlv0LTIklcTkIN2NSNwj/fsk/L8CqBedAn
feV0xUogB3Z2vuL/wMkYKTQ5tBOtGkA2YDHmuvyPUnU9OEgQ/Qd/CCwW+c1d3eAV
0gcC+Emo7Rdnuk3ksW5gh9vjkwKBgQDgvXKLiIyfpe+Gx6Fm93ZdPMlM9rZvt+dt
DaUklobdn45K1NafLgX5AfTB0szFrZV/K+l/IH5mJrddlZXEKuzaxWtBLBBoiTJv
rxza01VDeFu/l53ap+5jyBGzqY454I6pGwD0ct0ux6VAVRh/FwrJWHIeguQXyXJP
0fL9QXSDIQKBgCmDJ9QBi51kxgvHBL8oGIvM4wd5GxIVVMAZAk/PsrKvnSK6XDeF
WEcZBGEiA1eAOF1EldtIHs4WA7emlmjKvaHBWBlzInjHlJFc64JR5qfninnIwQ7l
/9B0FxCGxMEMYdtuKRJSS603etXwVSHEKPC6hLeVzeBfBlZylZZQx5OvAoGAB6hM
09ZGPFZSD/yTUkfSP6EHlti9JJdWik+xtcpvM/PwzDnuSiQuTeq0JTqCgaXFdzzO
yucXh3GAQ+8J2FJCGb4qRmEy+ezazBViXU5gFFlwftmypjWcmMfDWqTHVM+C7N4f
rTSQtrxUtBlyKTpmwq+By+pXzTuu6mtT5S8qwiECgYB9gKT3cZMCU3SaBM/Mp2fp
SlfOoJXmdLUQfMbramRIEnZaIP2jgLcdqfAK+KxFLeh8LB7e57oc5jD4w+Cigdyp
vbGYfCbJ7kwu5ezuEl2EFQtifUotI4DHibJJEYPqfrpNCE0kR0fF7+cT6RzKTm+p
t4KngSqVDYb10c4wcKOzrw==
-----END PRIVATE KEY-----
"@

# This script name, with various levels of details
$argv0 = Get-Item $MyInvocation.MyCommand.Definition
$script = $argv0.basename               # Ex: connect
$scriptName = $argv0.name               # Ex: connect.ps1
$scriptFullName = $argv0.fullname       # Ex: C:\Temp\connect.ps1

# Global settings
$serviceName = "HSConnect"        # A one-word name used for net start commands
$serviceDisplayName = "Hyperswitch Connect Service"
$ServiceDescription = "Start the hyper vpn connection before running cloud-init"
$pipeName = "Service_$serviceName"                # Named pipe name. Used for sending messages to the service task
$installDir = "${ENV:ProgramFiles}\$serviceName"  # Where to install the service files
$scriptCopy = "$installDir\$scriptName"
$exeName = "$serviceName.exe"
$exeFullName = "$installDir\$exeName"
$logDir = "$installDir\Logs"                      # Where to log the service messages
$logFile = "$logDir\$serviceName.log"
$logName = "Application"                          # Event Log name (Unrelated to the logFile!)

$tap_bin_dir = "C:\Program Files\Tap-Windows\bin"
$openvpn_conf_dir = "C:\Program Files\OpenVPN\config"
$openvpn_log_dir = "C:\Program Files\OpenVPN\log"

# If the -Version switch is specified, display the script version and exit.
if ($Version) {
  Write-Output $scriptVersion
  return
}

Function Now {
  Param (
    [Switch]$ms,        # Append milliseconds
    [Switch]$ns         # Append nanoseconds
  )
  $Date = Get-Date
  $now = ""
  $now += "{0:0000}-{1:00}-{2:00} " -f $Date.Year, $Date.Month, $Date.Day
  $now += "{0:00}:{1:00}:{2:00}" -f $Date.Hour, $Date.Minute, $Date.Second
  $nsSuffix = ""
  if ($ns) {
    if ("$($Date.TimeOfDay)" -match "\.\d\d\d\d\d\d") {
      $now += $matches[0]
      $ms = $false
    } else {
      $ms = $true
      $nsSuffix = "000"
    }
  }
  if ($ms) {
    $now += ".{0:000}$nsSuffix" -f $Date.MilliSecond
  }
  return $now
}

Function Log () {
  Param(
    [Parameter(Mandatory=$false, ValueFromPipeline=$true, Position=0)]
    [String]$string
  )
  if (!(Test-Path $logDir)) {
    New-Item -ItemType directory -Path $logDir | Out-Null
  }
  if ($String.length) {
    $string = "$(Now) $pid $userName $string"
  }
  $string | Out-File -enc ASCII -Append "$logFile"
}

Function CtrlSvc () {
  Set-Service cloudbase-init -startuptype "manual"
  Set-Service OpenVPNService -startuptype "manual"
  Set-Service OpenVPNServiceInteractive -startuptype "manual"
  Set-Service Ec2Config -startuptype "manual"
  Stop-Service cloudbase-init
  Stop-Service OpenVpnService
  Stop-Service OpenVPNServiceInteractive
  Stop-Service Ec2Config
  Stop-Process -processname "openvpn-gui"
}

Function WriteLine ([string]$message) {
    $message | Out-File -FilePath $openvpn_file_conf -Append -enc ASCII
}


$scriptCopyCname = $scriptCopy -replace "\\", "\\" # Double backslashes. (The first \\ is a regexp with \ escaped; The second is a plain string.)
$source = @"
  using System;
  using System.ServiceProcess;
  using System.Diagnostics;
  using System.Runtime.InteropServices;                                 // SET STATUS
  using System.ComponentModel;                                          // SET STATUS

  public enum ServiceType : int {                                       // SET STATUS [
    SERVICE_WIN32_OWN_PROCESS = 0x00000010,
    SERVICE_WIN32_SHARE_PROCESS = 0x00000020,
  };                                                                    // SET STATUS ]

  public enum ServiceState : int {                                      // SET STATUS [
    SERVICE_STOPPED = 0x00000001,
    SERVICE_START_PENDING = 0x00000002,
    SERVICE_STOP_PENDING = 0x00000003,
    SERVICE_RUNNING = 0x00000004,
    SERVICE_CONTINUE_PENDING = 0x00000005,
    SERVICE_PAUSE_PENDING = 0x00000006,
    SERVICE_PAUSED = 0x00000007,
  };                                                                    // SET STATUS ]

  [StructLayout(LayoutKind.Sequential)]                                 // SET STATUS [
  public struct ServiceStatus {
    public ServiceType dwServiceType;
    public ServiceState dwCurrentState;
    public int dwControlsAccepted;
    public int dwWin32ExitCode;
    public int dwServiceSpecificExitCode;
    public int dwCheckPoint;
    public int dwWaitHint;
  };                                                                    // SET STATUS ]

  public enum Win32Error : int { // WIN32 errors that we may need to use
    NO_ERROR = 0,
    ERROR_APP_INIT_FAILURE = 575,
    ERROR_FATAL_APP_EXIT = 713,
    ERROR_SERVICE_NOT_ACTIVE = 1062,
    ERROR_EXCEPTION_IN_SERVICE = 1064,
    ERROR_SERVICE_SPECIFIC_ERROR = 1066,
    ERROR_PROCESS_ABORTED = 1067,
  };

  public class Service_$serviceName : ServiceBase { // $serviceName may begin with a digit; The class name must begin with a letter
    private System.Diagnostics.EventLog eventLog;                       // EVENT LOG
    private ServiceStatus serviceStatus;                                // SET STATUS

    public Service_$serviceName() {
      ServiceName = "$serviceName";
      CanStop = true;
      CanPauseAndContinue = false;
      AutoLog = true;

      eventLog = new System.Diagnostics.EventLog();                     // EVENT LOG [
      if (!System.Diagnostics.EventLog.SourceExists(ServiceName)) {
        System.Diagnostics.EventLog.CreateEventSource(ServiceName, "$logName");
      }
      eventLog.Source = ServiceName;
      eventLog.Log = "$logName";                                        // EVENT LOG ]
      EventLog.WriteEntry(ServiceName, "$exeName $serviceName()");      // EVENT LOG
    }

    [DllImport("advapi32.dll", SetLastError=true)]                      // SET STATUS
    private static extern bool SetServiceStatus(IntPtr handle, ref ServiceStatus serviceStatus);

    protected override void OnStart(string [] args) {
      EventLog.WriteEntry(ServiceName, "$exeName OnStart() // Entry. Starting script '$scriptCopyCname' -Start"); // EVENT LOG
      // Set the service state to Start Pending.                        // SET STATUS [
      // Only useful if the startup time is long. Not really necessary here for a 2s startup time.
      serviceStatus.dwServiceType = ServiceType.SERVICE_WIN32_OWN_PROCESS;
      serviceStatus.dwCurrentState = ServiceState.SERVICE_START_PENDING;
      serviceStatus.dwWin32ExitCode = 0;
      serviceStatus.dwWaitHint = 2000; // It takes about 2 seconds to start PowerShell
      SetServiceStatus(ServiceHandle, ref serviceStatus);               // SET STATUS ]
      // Start a child process with another copy of this script
      try {
        Process p = new Process();
        // Redirect the output stream of the child process.
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.RedirectStandardOutput = true;
        p.StartInfo.FileName = "PowerShell.exe";
        p.StartInfo.Arguments = "-ExecutionPolicy Bypass -c & '$scriptCopyCname' -Start"; // Works if path has spaces, but not if it contains ' quotes.
        p.Start();
        // Read the output stream first and then wait. (To avoid deadlocks says Microsoft!)
        string output = p.StandardOutput.ReadToEnd();
        // Wait for the completion of the script startup code, that launches the -Service instance
        p.WaitForExit();
        if (p.ExitCode != 0) throw new Win32Exception((int)(Win32Error.ERROR_APP_INIT_FAILURE));
        // Success. Set the service state to Running.                   // SET STATUS
        serviceStatus.dwCurrentState = ServiceState.SERVICE_RUNNING;    // SET STATUS
      } catch (Exception e) {
        EventLog.WriteEntry(ServiceName, "$exeName OnStart() // Failed to start $scriptCopyCname. " + e.Message, EventLogEntryType.Error); // EVENT LOG
        // Change the service state back to Stopped.                    // SET STATUS [
        serviceStatus.dwCurrentState = ServiceState.SERVICE_STOPPED;
        Win32Exception w32ex = e as Win32Exception; // Try getting the WIN32 error code
        if (w32ex == null) { // Not a Win32 exception, but maybe the inner one is...
          w32ex = e.InnerException as Win32Exception;
        }
        if (w32ex != null) {    // Report the actual WIN32 error
          serviceStatus.dwWin32ExitCode = w32ex.NativeErrorCode;
        } else {                // Make up a reasonable reason
          serviceStatus.dwWin32ExitCode = (int)(Win32Error.ERROR_APP_INIT_FAILURE);
        }                                                               // SET STATUS ]
      } finally {
        serviceStatus.dwWaitHint = 0;                                   // SET STATUS
        SetServiceStatus(ServiceHandle, ref serviceStatus);             // SET STATUS
        EventLog.WriteEntry(ServiceName, "$exeName OnStart() // Exit"); // EVENT LOG
      }
    }

    protected override void OnStop() {
      EventLog.WriteEntry(ServiceName, "$exeName OnStop() // Entry");   // EVENT LOG
      // Start a child process with another copy of ourselves
      Process p = new Process();
      // Redirect the output stream of the child process.
      p.StartInfo.UseShellExecute = false;
      p.StartInfo.RedirectStandardOutput = true;
      p.StartInfo.FileName = "PowerShell.exe";
      p.StartInfo.Arguments = "-c & '$scriptCopyCname' -Stop"; // Works if path has spaces, but not if it contains ' quotes.
      p.Start();
      // Read the output stream first and then wait.
      string output = p.StandardOutput.ReadToEnd();
      // Wait for the PowerShell script to be fully stopped.
      p.WaitForExit();
      // Change the service state back to Stopped.                      // SET STATUS
      serviceStatus.dwCurrentState = ServiceState.SERVICE_STOPPED;      // SET STATUS
      SetServiceStatus(ServiceHandle, ref serviceStatus);               // SET STATUS
      EventLog.WriteEntry(ServiceName, "$exeName OnStop() // Exit");    // EVENT LOG
    }

    public static void Main() {
      System.ServiceProcess.ServiceBase.Run(new Service_$serviceName());
    }
  }
"@

#-----------------------------------------------------------------------------#
#                                                                             #
#   Function        Main                                                      #
#                                                                             #
#   Description     Execute the specified actions                             #
#                                                                             #
#   Arguments       See the Param() block at the top of this script           #
#                                                                             #
#   Notes                                                                     #
#                                                                             #
#   History                                                                   #
#                                                                             #
#-----------------------------------------------------------------------------#

# Check if we're running as a real user, or as the SYSTEM = As a service
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$userName = $identity.Name      # Ex: "NT AUTHORITY\SYSTEM" or "Domain\Administrator"
$authority,$name = $username -split "\\"
$isSystem = $identity.IsSystem # Do not test ($userName -eq "NT AUTHORITY\SYSTEM"), as this fails in non-English systems.
# Log "# `$userName = `"$userName`" ; `$isSystem = $isSystem"

if ($Setup) {Log ""}    # Insert one blank line to separate test sessions logs
Log $MyInvocation.Line # The exact command line that was used to start us

# The following commands write to the event log, but we need to make sure the connect source is defined.
New-EventLog -LogName $logName -Source $serviceName -ea SilentlyContinue

# Workaround for PowerShell v2 bug: $PSCmdlet Not yet defined in Param() block
$Status = ($PSCmdlet.ParameterSetName -eq 'Status')

if ($Start) {                   # Start the service
  if ($isSystem) { # If running as SYSTEM, ie. invoked as a service
    # do the stuff: configure openvpn and start it...
    Log "---------------------  Begin ---------------------"
    CtrlSvc

    netsh interface ipv4 set address name=Ethernet source=dhcp

    Log ""

    Log "OpenVPN service stopped"

    # user data format:
    # hsservers0 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
    # mac0 = 00:00:00:00:00:00
    # port0 = XXXX
    # hsservers1 = xxx.xxx.xxx.xxx, xxx.xxx.xxx.xxx
    # mac1 = 00:00:00:00:00:00
    # port1 = XXXX

    $UserData = Invoke-RestMethod 'http://169.254.169.254/1.0/user-data'
    Log "user data: $UserData"

    $userdata = ConvertFrom-StringData -StringData $UserData

    $i = 0
    $hsservers = $userdata."hsservers$i"
    $mac = $userdata."mac$i"
    $port = $userdata."port$i"
    $need_restart = $false

    $n_eth = "Ethernet"
    Log "n_eth : $n_eth"

    del "$openvpn_conf_dir\c-hs-*.ovpn"
    del "$openvpn_log_dir\c-hs-*.log"

    While ("$mac" -ne "") {

        Log "Port: $i"
        Log "mac: '$mac'"
        Log "hsservers: '$hsservers'"
        Log "port: '$port'"

        $hsservers = $hsservers -split ","
        $openvpn_file_conf = "c-hs-" + $i + ".ovpn"

        $vpn_ind = $i + 2
        $vpn_eth = "Ethernet " + $vpn_ind

        Log "vpn_eth: '$vpn_eth'"
        $vpn_nic_exist = openvpn --show-adapters | findstr /R /C:"$vpn_eth"
        if ("$vpn_nic_exist" -eq "") {
            cd $tap_bin_dir
            .\tapinstall.exe install "C:\Program Files\TAP-Windows\driver\OemVista.inf" tap0901
        }
        cd $openvpn_conf_dir
        WriteLine "client"
        WriteLine "pull"
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
        WriteLine "redirect-gateway local"

        # search the reg key
        $d_id_0 = "ROOT\NET\000" + $i
        Log "d_id_0: '$d_id_0'"
        for ($a = 10; $a -le 30; $a++){
            $reg_key = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}\00" + $a
            Log "regkey: '$reg_key'"
            $d_id = (Get-ItemProperty -Path "$reg_key").DeviceInstanceID
            if ($d_id -eq $d_id_0) {
                Break
            }
        }
        if ($d_id -eq $d_id_0) {
            $cur_mac = (Get-ItemProperty -Path "$reg_key").MAC
            Log "mac: '$mac'"
            Log "cur_mac: '$cur_mac'"
            Log "reg_key: '$reg_key'"
            If ($cur_mac -ne $mac){
                netsh interface set interface "$vpn_eth" disable
                Log "Not same mac: Need restart"
                Remove-ItemProperty -Path $reg_key -Name "MAC"
                New-ItemProperty -Path $reg_key -Name "MAC" -Value "$mac"
                $need_restart = $true
            }
        }
        Get-NetAdapter | Where-Object -FilterScript {$_.Name -Eq "$vpn_eth"} | Set-NetIPInterface -InterfaceMetric 5
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
    Start-Service OpenVpnService
    Log ""

    $init_ok = findstr /R /C:"Initialization Sequence Completed" "C:\Program Files\OpenVPN\log\c-hs-0.log"
    while ($init_ok -eq ""){
        Log "waiting for connection..."
        Start-Sleep -s 2
        $init_ok = findstr /R /C:"Initialization Sequence Completed" "C:\Program Files\OpenVPN\log\c-hs-0.log"
    }
    Log "!!!connected!!!!"
    Start-Service cloudbase-init
    Log "--------------------- End ---------------------"

  } else {
    Write-Verbose "Starting service $serviceName"
    Write-EventLog -LogName $logName -Source $serviceName -EventId 1002 -EntryType Information -Message "$scriptName -Start: Starting service $serviceName"
    Start-Service $serviceName # Ask Service Control Manager to start it
  }
  return
}

if ($Stop) {                    # Stop the service
  if ($isSystem) { # If running as SYSTEM, ie. invoked as a service
    # Do whatever is necessary to stop the service script instance
    Write-EventLog -LogName $logName -Source $serviceName -EventId 1003 -EntryType Information -Message "$scriptName -Stop: Stopping script $scriptName -Service"
    Log "$scriptName -Stop: Stopping script $scriptName -Service"
    Stop-Service OpenVpnService
  } else {
    Write-Verbose "Stopping service $serviceName"
    Write-EventLog -LogName $logName -Source $serviceName -EventId 1004 -EntryType Information -Message "$scriptName -Stop: Stopping service $serviceName"
    Stop-Service $serviceName # Ask Service Control Manager to stop it
  }
  return
}

if ($Restart) {                 # Restart the service
  & $scriptFullName -Stop
  & $scriptFullName -Start
  return
}

if ($Status) {                  # Get the current service status
  try {
    $pss = Get-Service $serviceName -ea stop # Will error-out if not installed
  } catch {
    "Not Installed"
    return
  }
  $pss.Status
  return
}

if ($Setup) {                   # Install the service
 # set cloudbase-init/EC2-config/OpenVPN services to manual
 CtrlSvc
 # Check if it's necessary
  try {
    $pss = Get-Service $serviceName -ea stop # Will error-out if not installed
    # Check if this script is newer than the installed copy.
    if ((Get-Item $scriptCopy -ea SilentlyContinue).LastWriteTime -lt (Get-Item $scriptFullName -ea SilentlyContinue).LastWriteTime) {
      Write-Verbose "Service $serviceName is already Installed, but requires upgrade"
      & $scriptFullName -Remove
      throw "continue"
    } else {
      Write-Verbose "Service $serviceName is already Installed, and up-to-date"
    }
    exit 0
  } catch {
    # This is the normal case here. Do not throw or write any error!
    Write-Debug "Installation is necessary" # Also avoids a ScriptAnalyzer warning
    # And continue with the installation.
  }
  if (!(Test-Path $installDir)) {
    New-Item -ItemType directory -Path $installDir | Out-Null
  }
  # Copy the service script into the installation directory
  if ($ScriptFullName -ne $scriptCopy) {
    Write-Verbose "Installing $scriptCopy"
    Copy-Item $ScriptFullName $scriptCopy
  }
  # Generate the service .EXE from the C# source embedded in this script
  try {
    Write-Verbose "Compiling $exeFullName"
    Add-Type -TypeDefinition $source -Language CSharp -OutputAssembly $exeFullName -OutputType ConsoleApplication -ReferencedAssemblies "System.ServiceProcess" -Debug:$false
  } catch {
    $msg = $_.Exception.Message
    Write-error "Failed to create the $exeFullName service stub. $msg"
    exit 1
  }
  # Register the service
  Write-Verbose "Registering service $serviceName"
  $pss = New-Service $serviceName $exeFullName -DisplayName $serviceDisplayName -Description $ServiceDescription -StartupType Automatic

  $ca_crt | Out-File -FilePath "$openvpn_conf_dir\ca.crt" -enc ASCII
  $client_crt | Out-File -FilePath "$openvpn_conf_dir\client.crt" -enc ASCII
  $client_key | Out-File -FilePath "$openvpn_conf_dir\client.key" -enc ASCII
  return
}

if ($Remove) {                  # Uninstall the service
  # Check if it's necessary
  try {
    $pss = Get-Service $serviceName -ea stop # Will error-out if not installed
  } catch {
    Write-Verbose "Already uninstalled"
    return
  }
  Stop-Service $serviceName # Make sure it's stopped
  # In the absence of a Remove-Service applet, use sc.exe instead.
  Write-Verbose "Removing service $serviceName"
  $msg = sc.exe delete $serviceName
  if ($LastExitCode) {
    Write-Error "Failed to remove the service ${serviceName}: $msg"
    exit 1
  } else {
    Write-Verbose $msg
  }
  # Remove the installed files
  if (Test-Path $installDir) {
    foreach ($ext in ("exe", "pdb", "ps1")) {
      $file = "$installDir\$serviceName.$ext"
      if (Test-Path $file) {
        Write-Verbose "Deleting file $file"
        Remove-Item $file
      }
    }
    Remove-Item $scriptCopy
    Remove-Item $logFile
    Remove-Item $logDir
    Remove-Item $installDir
  }
  #Remoe the client cert/key/ca
  Remove-Item "$openvpn_conf_dir\ca.crt"
  Remove-Item "$openvpn_conf_dir\client.crt"
  Remove-Item "$openvpn_conf_dir\client.key"
  del "$openvpn_conf_dir\c-hs-*.ovpn"
  del "$openvpn_log_dir\c-hs-*.log"
  return
}

