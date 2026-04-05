$ErrorActionPreference = "Stop"

$python = "c:/Users/yassi/Menacraft-Hackathon/.venv/Scripts/python.exe"
$api = "http://127.0.0.1:8002/analyze/source"

$cases = @(
  @{ url = "https://bbc.com"; expected = "authentic" },
  @{ url = "https://instagram.com/instagram"; expected = "authentic" },
  @{ url = "https://bbc-news-live.com"; expected = "fake" },
  @{ url = "http://suspicious-news.com"; expected = "suspicious" },
  @{ url = "8.8.8.8"; expected = "fake" }
)

Write-Output "==============================================="
Write-Output "ClipTrust Judge Demo"
Write-Output "==============================================="

$pass = 0
foreach ($c in $cases) {
  $code = @"
import requests
r = requests.post('$api', json={'url': '$($c.url)'}, timeout=20)
j = r.json()
print(j['verdict'])
print(j['score'])
print(j.get('confidence', 'n/a'))
print(j['flags'][0] if j.get('flags') else 'no-flag')
"@

  $out = & $python -c $code
  $pred = $out[0]
  $score = $out[1]
  $confidence = $out[2]
  $flag = $out[3]
  $ok = $pred -eq $c.expected
  if ($ok) { $pass += 1 }

  Write-Output "URL: $($c.url)"
  Write-Output "Expected: $($c.expected) | Predicted: $pred | Score: $score | Confidence: $confidence | Pass: $ok"
  Write-Output "Top flag: $flag"
  Write-Output "---"
}

Write-Output "Demo pass rate: $pass/$($cases.Count)"
