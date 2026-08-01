Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$src = @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public class Win32Dump {
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr hWnd, EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] static extern int GetWindowThreadProcessId(IntPtr hWnd, out int pid);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    static string Text(IntPtr h) { var sb = new StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
    static string Cls(IntPtr h) { var sb = new StringBuilder(512); GetClassName(h, sb, 512); return sb.ToString(); }

    public static List<string> TopLevel() {
        var list = new List<string>();
        EnumWindows((h, l) => {
            int pid; GetWindowThreadProcessId(h, out pid);
            list.Add(string.Format("TOP | hwnd={0} | pid={1} | visible={2} | class={3} | text={4}",
                h, pid, IsWindowVisible(h), Cls(h), Text(h)));
            return true;
        }, IntPtr.Zero);
        return list;
    }

    public static List<string> Children(int pid) {
        var list = new List<string>();
        EnumWindows((h, l) => {
            int p; GetWindowThreadProcessId(h, out p);
            if (p != pid) return true;
            RECT r; GetWindowRect(h, out r);
            list.Add(string.Format("WIN | hwnd={0} | visible={1} | class={2} | text={3} | rect={4},{5},{6},{7}",
                h, IsWindowVisible(h), Cls(h), Text(h), r.L, r.T, r.R, r.B));
            EnumChildWindows(h, (c, l2) => {
                RECT rc; GetWindowRect(c, out rc);
                list.Add(string.Format("  CHILD | hwnd={0} | visible={1} | class={2} | text={3} | rect={4},{5},{6},{7}",
                    c, IsWindowVisible(c), Cls(c), Text(c), rc.L, rc.T, rc.R, rc.B));
                return true;
            }, IntPtr.Zero);
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
"@
Add-Type -TypeDefinition $src -Language CSharp

$out = "$env:USERPROFILE\Desktop\softone_dump.txt"
"=== SOFT1 PROCESSES ===" | Out-File -FilePath $out -Encoding utf8

$procs = Get-Process | Where-Object { $_.ProcessName -match '^(xplorer|Soft1|xVision)$' }
foreach ($p in $procs) {
    "PROC | name=$($p.ProcessName) | pid=$($p.Id) | title=$($p.MainWindowTitle)" | Out-File -FilePath $out -Append -Encoding utf8
}

$pid1 = ($procs | Select-Object -First 1).Id
if ($null -eq $pid1) {
    "NO SOFT1 PROCESS FOUND" | Out-File -FilePath $out -Append -Encoding utf8
} else {
    "" | Out-File -FilePath $out -Append -Encoding utf8
    "=== WIN32 WINDOW TREE (pid=$pid1) ===" | Out-File -FilePath $out -Append -Encoding utf8
    [Win32Dump]::Children($pid1) | Out-File -FilePath $out -Append -Encoding utf8

    "" | Out-File -FilePath $out -Append -Encoding utf8
    "=== UIA DESCENDANTS (pid=$pid1) ===" | Out-File -FilePath $out -Append -Encoding utf8
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $pid1)
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    foreach ($w in $wins) {
        "UIA WINDOW | name=$($w.Current.Name) | class=$($w.Current.ClassName)" | Out-File -FilePath $out -Append -Encoding utf8
        $all = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition)
        "  UIA COUNT=$($all.Count)" | Out-File -FilePath $out -Append -Encoding utf8
        foreach ($e in $all) {
            $c = $e.Current
            "  UIA | type=$($c.ControlType.ProgrammaticName) | name=$($c.Name) | autoid=$($c.AutomationId) | class=$($c.ClassName)" |
                Out-File -FilePath $out -Append -Encoding utf8
        }
    }
}

Get-Content $out | Select-Object -First 80
"----"
"FULL DUMP: $out"
