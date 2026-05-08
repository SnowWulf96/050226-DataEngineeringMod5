$ErrorActionPreference = "Stop"

# Hardcoded demo settings
$DataDir = "C:\Users\Admin\Desktop\DataEngineeringMod5\050226-DataEngineeringMod5\Day_4\data"
$SqlServer = "localhost,1433"
$DatabaseName = "DataEngineeringMod5_NiroshsLibrary"
$SqlUsername = "notsahonest"
$SqlPassword = "password"

Write-Host "Cleaning files in: $DataDir"

$filesToDelete = @(
    (Join-Path $DataDir "03_Library Systembook Cleaned.csv"),
    (Join-Path $DataDir "03_Library SystemCustomers Cleaned.csv"),
    (Join-Path $DataDir "transformation_metrics_all.csv")
)

foreach ($file in $filesToDelete) {
    if (Test-Path -LiteralPath $file) {
        Remove-Item -LiteralPath $file -Force
        Write-Host "Deleted: $file"
    }
}

$connBuilder = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
$connBuilder["Data Source"] = $SqlServer
$connBuilder["Initial Catalog"] = "master"
$connBuilder["Connect Timeout"] = 8
$connBuilder["Encrypt"] = $true
$connBuilder["TrustServerCertificate"] = $true

if ($SqlUsername -and $SqlPassword) {
    $connBuilder["Integrated Security"] = $false
    $connBuilder["User ID"] = $SqlUsername
    $connBuilder["Password"] = $SqlPassword
} else {
    $connBuilder["Integrated Security"] = $true
}

$dropQuery = @"
IF DB_ID(N'$DatabaseName') IS NOT NULL
BEGIN
    ALTER DATABASE [$DatabaseName] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [$DatabaseName];
END
"@

$connection = New-Object System.Data.SqlClient.SqlConnection($connBuilder.ConnectionString)
try {
    $connection.Open()
    $command = $connection.CreateCommand()
    $command.CommandText = $dropQuery
    [void]$command.ExecuteNonQuery()
    Write-Host "Dropped database (if it existed): $DatabaseName"
}
finally {
    if ($connection.State -ne [System.Data.ConnectionState]::Closed) {
        $connection.Close()
    }
    $connection.Dispose()
}

Write-Host "Cleanup complete"
