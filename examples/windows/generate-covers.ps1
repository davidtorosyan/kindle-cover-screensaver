# Example: regenerate Kindle covers from a Calibre library on Windows.
#
# Copy this file to generate-covers.local.ps1 (git-ignored), fill in the
# paths, and run it whenever your library changes (or schedule it with
# Task Scheduler).

$Library = "C:\path\to\Calibre Library"     # your Calibre library folder
$Output  = "\\your-server\share\kindle\covers"  # where the web server can see it

kindle-covers generate $Library $Output `
    --device kindle_paperwhite2 `
    --filter-column "Read" --filter-value "True" `
    --border-color black `
    --clean
