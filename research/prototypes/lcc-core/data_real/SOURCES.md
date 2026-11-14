# Real documents used for the extraction check

Retrieved 2026-11-14 with curl from the public URLs below, converted with `pdftotext` (reading order, no `-layout`), wrapped with front matter by `data_real/build_docs.py`. Treated as untrusted data (Python reading them runs with `-I`).

| Doc id | Title | URL | Terms note |
|---|---|---|---|
| ADIENT-SSM-Q-R10 | Adient Global Supplier Standards Manual, Quality chapter, Rev 10.0 (1 Apr 2023), 19 pp | https://www.adient.com/wp-content/uploads/2023/04/Adient-Global-Supplier-Standards-Manual-%E2%80%93-Quality-Chapter.pdf | Public download. Page footer reads "For External Distribution". No licence given; (c) Adient. Used for research only. |
| ADIENT-LTR-UC | Adient US LLC letter "UNAUTHORIZED CHANGES", 28 Apr 2023 | https://www.adient.com/wp-content/uploads/2023/05/NOTICE-Suppliers-Unauthorized-Changes-20230501-AM-Signed.pdf | Public download. Footer reads "Adient - CONFIDENTIAL" although the file is served publicly. No licence given. |
| ASTEMO-SCM-R4 | Astemo Supplier Change Management Guidebook, Rev 4.0 (Dec 2025), 58 pp | https://www.am.astemo.com/sites/default/files/2026-01/Supplier%20Change%20Management%20Guidebook_Rev4.0_2025%20%28AM%29.pdf | Public download. Slide footer reads "CONFIDENTIAL, (c) Astemo, Ltd. All rights reserved". No licence given. |
| FORD-573-18V806 | Ford Part 573 Safety Recall Report 18V-806 (14 Nov 2018) | https://static.nhtsa.gov/odi/rcl/2018/RCLRPT-18V806-3961.PDF | US federal regulatory filing published by NHTSA. |

Do not republish `raw/`, `docs/` or `out/` quotes beyond short excerpts: three of the four documents carry copyright or confidentiality marks and no reuse licence. Keep them out of the public hackathon repo (publish the script and the audit, not the files).
