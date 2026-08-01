$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path $PSScriptRoot -Parent
$dataDir = Join-Path $projectRoot 'data'
$pricePath = Join-Path $dataDir 'mandi_prices.csv'
$locationPath = Join-Path $dataDir 'farm_locations.json'

$cropOrder = @('tomato', 'onion', 'potato', 'paddy')
$cropBase = @{
    tomato = 1500
    onion  = 2000
    potato = 1100
    paddy  = 9500
}
$cropTrendScale = @{
    tomato = 36
    onion  = 26
    potato = 16
    paddy  = 90
}
$cropSpread = @{
    tomato = 180
    onion  = 170
    potato = 140
    paddy  = 360
}

$marketSpecs = @(
    [pscustomobject]@{ State = 'Maharashtra'; Market = 'Nashik APMC'; BaseAdjust = 0; TrendFactor = 1.00; Phase = 0.0 }
    [pscustomobject]@{ State = 'Maharashtra'; Market = 'Pune Market Yard'; BaseAdjust = 180; TrendFactor = 0.75; Phase = 0.8 }
    [pscustomobject]@{ State = 'Maharashtra'; Market = 'Lasalgaon Mandi'; BaseAdjust = 80; TrendFactor = 0.50; Phase = 1.6 }
    [pscustomobject]@{ State = 'Tamil Nadu'; Market = 'Koyambedu Market, Chennai'; BaseAdjust = -120; TrendFactor = -0.30; Phase = 0.4 }
    [pscustomobject]@{ State = 'Tamil Nadu'; Market = 'Madurai Mandi'; BaseAdjust = -160; TrendFactor = 0.10; Phase = 1.2 }
    [pscustomobject]@{ State = 'Tamil Nadu'; Market = 'Coimbatore Market'; BaseAdjust = -90; TrendFactor = 0.25; Phase = 2.0 }
    [pscustomobject]@{ State = 'Karnataka'; Market = 'KR Market, Bengaluru'; BaseAdjust = 60; TrendFactor = 0.45; Phase = 0.5 }
    [pscustomobject]@{ State = 'Karnataka'; Market = 'Hubballi APMC'; BaseAdjust = 20; TrendFactor = 0.65; Phase = 1.3 }
    [pscustomobject]@{ State = 'Punjab'; Market = 'Ludhiana Grain Market'; BaseAdjust = 120; TrendFactor = -0.10; Phase = 0.7 }
    [pscustomobject]@{ State = 'Punjab'; Market = 'Jalandhar APMC'; BaseAdjust = 90; TrendFactor = 0.20; Phase = 1.4 }
    [pscustomobject]@{ State = 'Uttar Pradesh'; Market = 'Lucknow APMC'; BaseAdjust = 40; TrendFactor = 0.55; Phase = 0.9 }
    [pscustomobject]@{ State = 'Uttar Pradesh'; Market = 'Kanpur Mandi'; BaseAdjust = 70; TrendFactor = 0.35; Phase = 1.7 }
)

$rows = New-Object 'System.Collections.Generic.List[object]'
$startDate = [datetime]'2026-07-19'

for ($dayIndex = 0; $dayIndex -lt 7; $dayIndex++) {
    $date = $startDate.AddDays($dayIndex).ToString('yyyy-MM-dd')
    foreach ($market in $marketSpecs) {
        foreach ($crop in $cropOrder) {
            $cropIndex = [array]::IndexOf($cropOrder, $crop)
            $wave = [math]::Round([math]::Sin((($dayIndex + 1) * 1.15) + $market.Phase + ($cropIndex * 0.35)) * ($cropSpread[$crop] * 0.18), 0)
            $modal = [math]::Round($cropBase[$crop] + $market.BaseAdjust + ($market.TrendFactor * $cropTrendScale[$crop] * $dayIndex) + $wave, 0)
            $spread = $cropSpread[$crop]
            $rows.Add([pscustomobject]@{
                date        = $date
                state       = $market.State
                market      = $market.Market
                crop        = $crop
                min_price   = [math]::Max(0, $modal - $spread)
                max_price   = $modal + $spread
                modal_price = $modal
            })
        }
    }
}

# PowerShell 5 writes a BOM for -Encoding utf8.  Write the CSV text ourselves
# with a BOM-free UTF-8 encoder so Python's standard csv reader sees `date`
# as the first header without needing an encoding-specific workaround.
$csvLines = @(
    $rows |
        Sort-Object date, state, market, crop |
        ConvertTo-Csv -NoTypeInformation
)
# Header fields are simple identifiers, so they do not need CSV quotes.  Data
# rows retain CSV quoting (needed for market names containing commas).
$csvLines[0] = 'date,state,market,crop,min_price,max_price,modal_price'
$priceCsvText = ($csvLines -join [Environment]::NewLine) + [Environment]::NewLine
Set-Content -LiteralPath $pricePath -Encoding Byte -Value ([System.Text.Encoding]::UTF8.GetBytes($priceCsvText))

$locations = @(
    [ordered]@{
        id = 'nashik_demo_village'
        display_name = 'Village near Nashik'
        state = 'Maharashtra'
        latitude = 20.015
        longitude = 73.790
        distances_km = [ordered]@{
            'Nashik APMC' = 5
            'Pune Market Yard' = 45
            'Lasalgaon Mandi' = 20
            'Koyambedu Market, Chennai' = 1170
            'Madurai Mandi' = 1030
            'Coimbatore Market' = 1080
            'KR Market, Bengaluru' = 980
            'Hubballi APMC' = 720
            'Ludhiana Grain Market' = 1370
            'Jalandhar APMC' = 1420
            'Lucknow APMC' = 1120
            'Kanpur Mandi' = 1090
        }
    }
    [ordered]@{
        id = 'pune_demo_village'
        display_name = 'Village near Pune'
        state = 'Maharashtra'
        latitude = 18.520
        longitude = 73.860
        distances_km = [ordered]@{
            'Nashik APMC' = 205
            'Pune Market Yard' = 12
            'Lasalgaon Mandi' = 235
            'Koyambedu Market, Chennai' = 1180
            'Madurai Mandi' = 1110
            'Coimbatore Market' = 1010
            'KR Market, Bengaluru' = 850
            'Hubballi APMC' = 630
            'Ludhiana Grain Market' = 1470
            'Jalandhar APMC' = 1520
            'Lucknow APMC' = 1290
            'Kanpur Mandi' = 1250
        }
    }
    [ordered]@{
        id = 'coimbatore_demo_village'
        display_name = 'Village near Coimbatore'
        state = 'Tamil Nadu'
        latitude = 11.020
        longitude = 76.960
        distances_km = [ordered]@{
            'Nashik APMC' = 1080
            'Pune Market Yard' = 1010
            'Lasalgaon Mandi' = 1050
            'Koyambedu Market, Chennai' = 510
            'Madurai Mandi' = 230
            'Coimbatore Market' = 15
            'KR Market, Bengaluru' = 350
            'Hubballi APMC' = 770
            'Ludhiana Grain Market' = 2700
            'Jalandhar APMC' = 2750
            'Lucknow APMC' = 2090
            'Kanpur Mandi' = 2050
        }
    }
    [ordered]@{
        id = 'madurai_demo_village'
        display_name = 'Village near Madurai'
        state = 'Tamil Nadu'
        latitude = 9.930
        longitude = 78.120
        distances_km = [ordered]@{
            'Nashik APMC' = 1030
            'Pune Market Yard' = 1110
            'Lasalgaon Mandi' = 1010
            'Koyambedu Market, Chennai' = 460
            'Madurai Mandi' = 18
            'Coimbatore Market' = 230
            'KR Market, Bengaluru' = 430
            'Hubballi APMC' = 840
            'Ludhiana Grain Market' = 2800
            'Jalandhar APMC' = 2850
            'Lucknow APMC' = 2200
            'Kanpur Mandi' = 2160
        }
    }
    [ordered]@{
        id = 'bengaluru_demo_village'
        display_name = 'Village near Bengaluru'
        state = 'Karnataka'
        latitude = 12.970
        longitude = 77.600
        distances_km = [ordered]@{
            'Nashik APMC' = 980
            'Pune Market Yard' = 850
            'Lasalgaon Mandi' = 940
            'Koyambedu Market, Chennai' = 360
            'Madurai Mandi' = 430
            'Coimbatore Market' = 350
            'KR Market, Bengaluru' = 8
            'Hubballi APMC' = 430
            'Ludhiana Grain Market' = 2050
            'Jalandhar APMC' = 2100
            'Lucknow APMC' = 1720
            'Kanpur Mandi' = 1680
        }
    }
    [ordered]@{
        id = 'hubballi_demo_village'
        display_name = 'Village near Hubballi'
        state = 'Karnataka'
        latitude = 15.360
        longitude = 75.120
        distances_km = [ordered]@{
            'Nashik APMC' = 720
            'Pune Market Yard' = 560
            'Lasalgaon Mandi' = 620
            'Koyambedu Market, Chennai' = 840
            'Madurai Mandi' = 910
            'Coimbatore Market' = 770
            'KR Market, Bengaluru' = 420
            'Hubballi APMC' = 12
            'Ludhiana Grain Market' = 1950
            'Jalandhar APMC' = 2000
            'Lucknow APMC' = 1560
            'Kanpur Mandi' = 1520
        }
    }
    [ordered]@{
        id = 'ludhiana_demo_village'
        display_name = 'Village near Ludhiana'
        state = 'Punjab'
        latitude = 30.910
        longitude = 75.860
        distances_km = [ordered]@{
            'Nashik APMC' = 1350
            'Pune Market Yard' = 1470
            'Lasalgaon Mandi' = 1400
            'Koyambedu Market, Chennai' = 2600
            'Madurai Mandi' = 2700
            'Coimbatore Market' = 2550
            'KR Market, Bengaluru' = 2050
            'Hubballi APMC' = 1850
            'Ludhiana Grain Market' = 10
            'Jalandhar APMC' = 90
            'Lucknow APMC' = 390
            'Kanpur Mandi' = 430
        }
    }
    [ordered]@{
        id = 'jalandhar_demo_village'
        display_name = 'Village near Jalandhar'
        state = 'Punjab'
        latitude = 31.330
        longitude = 75.580
        distances_km = [ordered]@{
            'Nashik APMC' = 1420
            'Pune Market Yard' = 1520
            'Lasalgaon Mandi' = 1470
            'Koyambedu Market, Chennai' = 2680
            'Madurai Mandi' = 2780
            'Coimbatore Market' = 2620
            'KR Market, Bengaluru' = 2100
            'Hubballi APMC' = 1900
            'Ludhiana Grain Market' = 90
            'Jalandhar APMC' = 10
            'Lucknow APMC' = 430
            'Kanpur Mandi' = 470
        }
    }
    [ordered]@{
        id = 'lucknow_demo_village'
        display_name = 'Village near Lucknow'
        state = 'Uttar Pradesh'
        latitude = 26.850
        longitude = 80.950
        distances_km = [ordered]@{
            'Nashik APMC' = 1120
            'Pune Market Yard' = 1290
            'Lasalgaon Mandi' = 1150
            'Koyambedu Market, Chennai' = 1750
            'Madurai Mandi' = 1850
            'Coimbatore Market' = 1710
            'KR Market, Bengaluru' = 1680
            'Hubballi APMC' = 1520
            'Ludhiana Grain Market' = 390
            'Jalandhar APMC' = 430
            'Lucknow APMC' = 15
            'Kanpur Mandi' = 110
        }
    }
    [ordered]@{
        id = 'kanpur_demo_village'
        display_name = 'Village near Kanpur'
        state = 'Uttar Pradesh'
        latitude = 26.450
        longitude = 80.330
        distances_km = [ordered]@{
            'Nashik APMC' = 1090
            'Pune Market Yard' = 1250
            'Lasalgaon Mandi' = 1120
            'Koyambedu Market, Chennai' = 1720
            'Madurai Mandi' = 1820
            'Coimbatore Market' = 1680
            'KR Market, Bengaluru' = 1650
            'Hubballi APMC' = 1500
            'Ludhiana Grain Market' = 430
            'Jalandhar APMC' = 470
            'Lucknow APMC' = 110
            'Kanpur Mandi' = 12
        }
    }
)

# Match the CSV fixture: PowerShell 5's -Encoding utf8 emits a BOM, so use
# an explicit UTF-8 encoder to keep the JSON portable for standard parsers.
$locationsJson = $locations | ConvertTo-Json -Depth 6
Set-Content -LiteralPath $locationPath -Encoding Byte -Value ([System.Text.Encoding]::UTF8.GetBytes($locationsJson))
