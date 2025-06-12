#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PowerShell script to run the Channel Latency Monitor for BINARY TRADING CLUB

.DESCRIPTION
    This script provides an easy way to run the channel latency monitor with
    different options for testing the BINARY TRADING CLUB channel performance.

.PARAMETER TestType
    The type of test to run:
    - Quick: Quick test (2 minutes)
    - Full: Full monitoring (15 minutes)
    - Reception: Message reception test only
    - Parsing: Signal parsing test only
    - Comprehensive: Complete analysis
    - Custom: Custom duration monitoring

.PARAMETER Duration
    Custom duration in minutes (only used with -TestType Custom)

.EXAMPLE
    .\Run-ChannelLatencyMonitor.ps1 -TestType Quick
    Run a quick 2-minute test

.EXAMPLE
    .\Run-ChannelLatencyMonitor.ps1 -TestType Custom -Duration 30
    Run custom monitoring for 30 minutes

.EXAMPLE
    .\Run-ChannelLatencyMonitor.ps1 -TestType Comprehensive
    Run comprehensive channel analysis
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Quick", "Full", "Reception", "Parsing", "Comprehensive", "Custom", "Test")]
    [string]$TestType = "Quick",
    
    [Parameter(Mandatory=$false)]
    [int]$Duration = 15
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-PythonEnvironment {
    Write-ColorOutput "🔍 Checking Python environment..." $Cyan
    
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✅ Python found: $pythonVersion" $Green
        
        # Check if required packages are installed
        $packages = @("telethon", "asyncio", "statistics")
        foreach ($package in $packages) {
            try {
                python -c "import $package" 2>$null
                Write-ColorOutput "✅ Package '$package' is available" $Green
            }
            catch {
                Write-ColorOutput "⚠️  Package '$package' may not be installed" $Yellow
            }
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ Python not found or not accessible" $Red
        Write-ColorOutput "Please ensure Python is installed and in your PATH" $Red
        return $false
    }
}

function Test-ConfigurationFiles {
    Write-ColorOutput "🔍 Checking configuration files..." $Cyan
    
    $configFiles = @(
        "config/telegram_config.json",
        "config/pocket_option_config.json"
    )
    
    $allFilesExist = $true
    
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Write-ColorOutput "✅ Found: $file" $Green
        }
        else {
            Write-ColorOutput "❌ Missing: $file" $Red
            $allFilesExist = $false
        }
    }
    
    return $allFilesExist
}

function Start-ChannelLatencyMonitor {
    param(
        [string]$Type,
        [int]$CustomDuration
    )
    
    Write-ColorOutput "`n🚀 Starting Channel Latency Monitor..." $Cyan
    Write-ColorOutput "📊 Test Type: $Type" $Cyan
    
    try {
        switch ($Type) {
            "Test" {
                Write-ColorOutput "🧪 Running quick verification test..." $Cyan
                python test_channel_monitor.py
            }
            "Quick" {
                Write-ColorOutput "⚡ Running quick live test (2 minutes)..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_quick():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            results = await monitor.monitor_live_channel_performance(2)
            monitor.print_performance_report(results)
    finally:
        await monitor.cleanup()

asyncio.run(run_quick())
"
            }
            "Full" {
                Write-ColorOutput "🕐 Running full monitoring (15 minutes)..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_full():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            results = await monitor.monitor_live_channel_performance(15)
            monitor.print_performance_report(results)
    finally:
        await monitor.cleanup()

asyncio.run(run_full())
"
            }
            "Reception" {
                Write-ColorOutput "📱 Testing message reception latency..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_reception():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            result = await monitor.measure_message_reception_latency(15)
            if result['success']:
                print(f'📊 Reception Results:')
                print(f'   Average: {result[\"avg\"]:.2f}ms')
                print(f'   Min: {result[\"min\"]:.2f}ms')
                print(f'   Max: {result[\"max\"]:.2f}ms')
                rating, verdict, recommendation = monitor.assess_performance(result['avg'])
                print(f'🏆 Performance: {rating}')
                print(f'   {recommendation}')
    finally:
        await monitor.cleanup()

asyncio.run(run_reception())
"
            }
            "Parsing" {
                Write-ColorOutput "🔍 Testing signal parsing performance..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_parsing():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            results = await monitor.test_signal_parsing_performance()
            monitor.print_performance_report(results)
    finally:
        await monitor.cleanup()

asyncio.run(run_parsing())
"
            }
            "Comprehensive" {
                Write-ColorOutput "🔍 Running comprehensive channel analysis..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_comprehensive():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            results = await monitor.run_comprehensive_channel_analysis()
            print(f'🎯 COMPREHENSIVE ANALYSIS COMPLETE')
            if 'assessment' in results:
                print(f'   Overall Rating: {results[\"assessment\"][\"rating\"]}')
                print(f'   Recommendation: {results[\"assessment\"][\"recommendation\"]}')
    finally:
        await monitor.cleanup()

asyncio.run(run_comprehensive())
"
            }
            "Custom" {
                Write-ColorOutput "⏱️ Running custom monitoring ($CustomDuration minutes)..." $Cyan
                python -c "
import asyncio
from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def run_custom():
    monitor = BinaryTradingClubLatencyMonitor()
    try:
        if await monitor.initialize():
            results = await monitor.monitor_live_channel_performance($CustomDuration)
            monitor.print_performance_report(results)
    finally:
        await monitor.cleanup()

asyncio.run(run_custom())
"
            }
        }
        
        Write-ColorOutput "`n✅ Channel latency monitoring completed successfully!" $Green
    }
    catch {
        Write-ColorOutput "`n❌ Error running channel latency monitor:" $Red
        Write-ColorOutput $_.Exception.Message $Red
        exit 1
    }
}

# Main execution
Write-ColorOutput "🎯 BINARY TRADING CLUB CHANNEL LATENCY MONITOR" $Cyan
Write-ColorOutput "=" * 60 $Cyan

# Check Python environment
if (-not (Test-PythonEnvironment)) {
    exit 1
}

# Check configuration files
if (-not (Test-ConfigurationFiles)) {
    Write-ColorOutput "`n❌ Missing required configuration files" $Red
    Write-ColorOutput "Please ensure config/telegram_config.json and config/pocket_option_config.json exist" $Red
    exit 1
}

# Show test options if no specific type provided
if ($TestType -eq "Quick" -and $args.Count -eq 0) {
    Write-ColorOutput "`n📋 Available Test Types:" $Yellow
    Write-ColorOutput "  Test         - Quick verification test" $Yellow
    Write-ColorOutput "  Quick        - Quick live test (2 minutes)" $Yellow
    Write-ColorOutput "  Full         - Full monitoring (15 minutes)" $Yellow
    Write-ColorOutput "  Reception    - Message reception test only" $Yellow
    Write-ColorOutput "  Parsing      - Signal parsing test only" $Yellow
    Write-ColorOutput "  Comprehensive - Complete analysis" $Yellow
    Write-ColorOutput "  Custom       - Custom duration monitoring" $Yellow
    Write-ColorOutput "`nExamples:" $Yellow
    Write-ColorOutput "  .\Run-ChannelLatencyMonitor.ps1 -TestType Test" $Yellow
    Write-ColorOutput "  .\Run-ChannelLatencyMonitor.ps1 -TestType Custom -Duration 30" $Yellow
    Write-ColorOutput "`nRunning default Quick test..." $Yellow
}

# Start the monitoring
Start-ChannelLatencyMonitor -Type $TestType -CustomDuration $Duration

Write-ColorOutput "`n🎉 Channel latency monitoring session complete!" $Green
Write-ColorOutput "📊 Check the generated JSON files for detailed results" $Cyan
