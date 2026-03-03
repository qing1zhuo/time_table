Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "run_desktop_app.bat" & Chr(34), 0
Set WshShell = Nothing