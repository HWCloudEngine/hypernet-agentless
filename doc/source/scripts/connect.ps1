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
  $string | Out-File -Encoding ASCII -Append "$logFile"
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
    $message | Out-File -FilePath $openvpn_file_conf -Append -enc UTF8
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

    $tap_bin_dir = "C:\Program Files\Tap-Windows\bin"
    $openvpn_conf_dir = "C:\Program Files\OpenVPN\config"
    $openvpn_log_dir = "C:\Program Files\OpenVPN\log"

    del $openvpn_conf_dir"\c-hs-*.ovpn"
    del $openvpn_log_dir"\c-hs-*.log"

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
    if (!(@(Get-ChildItem $installDir -ea SilentlyContinue)).Count) {
      Write-Verbose "Removing directory $installDir"
      Remove-Item $installDir
    }
  }
  return
}

