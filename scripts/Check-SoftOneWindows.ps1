# Diag: which window eats desktop-icon clicks while SoftOne (C:\Soft1) is open.
# Run WHILE the problem occurs. Read-only: only inspects windows/cursor state.
# ASCII-only messages so it parses under Windows PowerShell 5.1 without BOM issues.

[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public struct RECT { public int Left, Top, Right, Bottom; }
public class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int i);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsHungAppWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetClipCursor(out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr GetCapture();
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(System.IntPtr ctx);
  [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
  [DllImport("user32.dll")] public static extern bool GetGUIThreadInfo(uint tid, ref GUITHREADINFO g);
}
public struct POINT { public int X, Y; }
[StructLayout(LayoutKind.Sequential)]
public struct GUITHREADINFO {
  public int cbSize; public int flags;
  public System.IntPtr hwndActive, hwndFocus, hwndCapture, hwndMenuOwner, hwndMoveSize, hwndCaret;
  public RECT rcCaret;
}
"@

# Make this process per-monitor DPI aware so window/cursor rects come back in
# physical pixels (otherwise user32 virtualizes them and the clip check lies).
[W]::SetProcessDpiAwarenessContext([System.IntPtr]::new(-4)) | Out-Null

# Soft1-related process ids (client + helpers)
$s1names = @('xplorer','s1access','s1agent','xretail','AutoUpd','cshcontrol','DEVIN-PDF','pbxmonitor','S1QView')
$s1pids = Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like 'C:\Soft1*' -or $s1names -contains $_.Name } |
  Select-Object -ExpandProperty Id

Write-Host "=== Soft1 processes: $($s1pids -join ', ') ==="

# Cursor clip: if rect is smaller than the virtual screen -> cursor is trapped
$clip = New-Object RECT
[W]::GetClipCursor([ref]$clip) | Out-Null
$vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
Write-Host "ClipCursor rect : L=$($clip.Left) T=$($clip.Top) R=$($clip.Right) B=$($clip.Bottom)"
Write-Host "Virtual screen  : L=$($vs.Left) T=$($vs.Top) R=$($vs.Right) B=$($vs.Bottom)"
if ($clip.Right - $clip.Left -lt $vs.Width -or $clip.Bottom - $clip.Top -lt $vs.Height) {
  Write-Host ">>> CURSOR TRAPPED (ClipCursor) - some app locked it to a region" -ForegroundColor Yellow
}

$cap = [W]::GetCapture()
if ($cap -ne [IntPtr]::Zero) {
  $cpid = 0; [W]::GetWindowThreadProcessId($cap, [ref]$cpid) | Out-Null
  $p = Get-Process -Id $cpid -ErrorAction SilentlyContinue
  Write-Host ">>> GetCapture: window $cap owned by PID $cpid ($($p.Name)) - holds ALL mouse input" -ForegroundColor Yellow
} else {
  Write-Host "GetCapture: no window holds the mouse"
}

$fg = [W]::GetForegroundWindow(); $fgpid = 0
[W]::GetWindowThreadProcessId($fg, [ref]$fgpid) | Out-Null
$fgp = Get-Process -Id $fgpid -ErrorAction SilentlyContinue
Write-Host "Foreground window: PID $fgpid ($($fgp.Name))"

Write-Host "`n=== Windows that could block clicks (topmost or Soft1-owned) ==="
$sb = New-Object System.Text.StringBuilder 256
$cb = [W+EnumProc]{ param($h,$l)
  $wpid = 0; [W]::GetWindowThreadProcessId($h,[ref]$wpid) | Out-Null
  $ex  = [W]::GetWindowLong($h, -20)           # GWL_EXSTYLE
  $topmost  = ($ex -band 0x8)    -ne 0         # WS_EX_TOPMOST
  $isS1     = $s1pids -contains $wpid
  if (-not $topmost -and -not $isS1) { return $true }
  $r = New-Object RECT; [W]::GetWindowRect($h,[ref]$r) | Out-Null
  $w = $r.Right-$r.Left; $ht = $r.Bottom-$r.Top
  if ($w -le 0 -or $ht -le 0) { return $true }
  [W]::GetWindowText($h,$sb,$sb.Capacity) | Out-Null
  $proc = Get-Process -Id $wpid -ErrorAction SilentlyContinue
  $vis  = [W]::IsWindowVisible($h); $hung = [W]::IsHungAppWindow($h)
  $mark = if ($isS1) { '[SOFT1]' } else { '' }
  Write-Host ("{0} hwnd={1,-10} pid={2,-6} {3,-22} topmost={4,-5} visible={5,-5} hung={6,-5} rect=({7},{8})-({9},{10}) {11}x{12} title='{13}'" -f `
    $mark,$h,$wpid,$proc.Name,$topmost,$vis,$hung,$r.Left,$r.Top,$r.Right,$r.Bottom,$w,$ht,$sb.ToString())
  return $true
}
[W]::EnumWindows($cb, [IntPtr]::Zero) | Out-Null

# --- GUI thread state of Soft1 processes: a thread stuck in menu/movesize mode
# swallows all outside clicks until dismissed.
Write-Host "`n=== GUI thread state of Soft1 processes (menu/movesize flags) ==="
$flagNames = @{0x2='INMOVESIZE';0x4='INMENUMODE';0x8='SYSTEMMENUMODE';0x10='POPUPMENUMODE'}
foreach ($sp in $s1pids) {
  $proc = Get-Process -Id $sp -ErrorAction SilentlyContinue
  foreach ($t in $proc.Threads) {
    $g = New-Object GUITHREADINFO; $g.cbSize = [Runtime.InteropServices.Marshal]::SizeOf($g)
    if ([W]::GetGUIThreadInfo([uint32]$t.Id, [ref]$g)) {
      $names = ($flagNames.GetEnumerator() | Where-Object { $g.flags -band $_.Key } | ForEach-Object { $_.Value }) -join ','
      if ($names) { Write-Host ("pid={0} ({1}) tid={2} flags=0x{3:x} [{4}] menuOwner={5} capture={6}" -f $sp,$proc.Name,$t.Id,$g.flags,$names,$g.hwndMenuOwner,$g.hwndCapture) }
    }
  }
}

# --- Dead-zone map: probe a grid over every monitor; '.'=desktop/explorer,
# 'S'=Soft1-owned window gets the input there, 'X'=other app.
Write-Host "`n=== Input map (what receives a click at each spot) ==="
$pt = New-Object POINT; $wp2 = 0
foreach ($scr in [System.Windows.Forms.Screen]::AllScreens) {
  $b = $scr.Bounds
  Write-Host "Screen $($scr.DeviceName) bounds=($($b.Left),$($b.Top))-($($b.Right),$($b.Bottom))  primary=$($scr.Primary)"
  $stepX = [Math]::Max(80, [int]($b.Width/48)); $stepY = [Math]::Max(80, [int]($b.Height/27))
  $anoms = @{}
  for ($y=$b.Top+40; $y -lt $b.Bottom-40; $y+=$stepY) {
    $row=''
    for ($x=$b.Left+40; $x -lt $b.Right-40; $x+=$stepX) {
      $pt.X=$x; $pt.Y=$y
      $h=[W]::WindowFromPoint($pt); $wp2=0
      if ($h -ne [IntPtr]::Zero) { [W]::GetWindowThreadProcessId($h,[ref]$wp2)|Out-Null }
      $pn=(Get-Process -Id $wp2 -ErrorAction SilentlyContinue).Name
      $c = if ($s1pids -contains $wp2) {'S'} elseif ($pn -eq 'explorer' -or $h -eq [IntPtr]::Zero) {'.'} else {'X'}
      if ($c -ne '.') { $anoms["$pn($wp2)"]++ }
      $row += $c
    }
    Write-Host $row
  }
  if ($anoms.Count) { Write-Host ("non-desktop owners: " + (($anoms.GetEnumerator() | ForEach-Object { "$($_.Key)x$($_.Value)" }) -join ', ')) }
}
Write-Host "`nLegend: '.' desktop ok | 'S' Soft1 window eats input there | 'X' other app"
