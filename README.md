# Priva VP9508 Greenhouse Sensor Dashboard

## Haqqında
Bu vebsayt 6+ il (2020-2026) ərzindəki Priva VP9508 istixana iqlim nəzarət sisteminin sensor datalarını analiz edir.

## Texniki Detallar
- **Sistem**: Priva Integro / Connext VP9508
- **Fayl formatı**: Binary .dlt (indeks) + .dof (verilənlər) - zlib sıxılmış
- **Rekord strukturu**: int32(unix_timestamp) + double(value) = 12 bayt
- **Kanallar**: 371 unikal sensor kanali
- **Tarix aralığı**: 25 Yanvar 2020 → 25 Aprel 2026 (588 gün)
- **Ümumi ölçümlər**: ~6.5 milyon rekord
- **Interval**: ~5 dəqiqəlik ölçmə intervalı

## Sensor Növləri
- Xarici hava: temperatur, külək, radiasiya, yağış, don
- İstixana: temperatur (4 bölmə), rütubət (4 bölmə)
- Isıtma: qazan temperaturu, boru temperaturu, bufer dolumu
- Ventilyasiya: açılma faizi, küləyin istiqaməti
- CO₂: konsentrasiya, dozaj nəzarəti
- Su: su temperaturu, EC, pH, axın sürəti
- Enerji: qaz sərfi, ümumi qaz

## Necə işlətmək
```bash
pip install flask
python3 run_dashboard.py
# Brauzer: http://localhost:5000
```
