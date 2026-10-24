# HISTORY CHECK 1024

DB: FOUNTOUKAS @ .\SOFTONE - COMPANY=1001 - read-only (devin_ro). Date: 2026-10-24.

## Q1 - FINDOC x TRDR x MTRLINES (SODTYPE 12,16 / codes 0191,0212,0049,0133,0025)

```sql
SELECT TOP 400 T.SODTYPE, T.CODE AS TRDR, T.NAME, F.SOSOURCE, F.FINCODE, CONVERT(char(10),F.TRNDATE,103) AS DT, M.CODE AS ITEM, M.NAME AS ITEMNAME, L.QTY1, L.PRICE, L.LINEVAL, F.SUMAMNT FROM FINDOC F JOIN TRDR T ON T.TRDR=F.TRDR JOIN MTRLINES L ON L.FINDOC=F.FINDOC JOIN MTRL M ON M.MTRL=L.MTRL WHERE F.COMPANY=1001 AND T.CODE IN ('0191','0212','0049','0133','0025') AND T.SODTYPE IN (12,16) ORDER BY T.SODTYPE, T.CODE, F.TRNDATE DESC```

Output - 130 rows (verbatim sqlcmd):

```
SODTYPE|TRDR|NAME|SOSOURCE|FINCODE|DT|ITEM|ITEMNAME|QTY1|PRICE|LINEVAL|SUMAMNT
-------|----|----|--------|-------|--|----|--------|----|-----|-------|-------
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03757|SM 7000-PLUS SKEWERING MACHINE WITH GUIDE RAIL|1.0|154800.0|77400.0|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|02808|ΞΥΛΟΚΟΥΤΟ ΓΙΑ SM 7000|1.0|1060.0|954.0|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|00107|ΚΙΤ ΠΑΡΑΓΩΓΗΣ ΦΟΡΜΑΤ 27|1.0|5255.0|4729.5|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|02821|ΚΙΒΩΤΙΔΙΟ ΦΟΡΜΑΤ 27 210|5.0|1403.0|6313.5|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03871|ΚΙΒΩΤΙΔΙΟ ΦΟΡΜΑΤ 27 160|5.0|1109.7|4993.6499999999996|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03779|ΚΑΠΑΚΙ ΦΟΡΜΑΤ 27 / -10mm|2.0|477.0|858.60000000000002|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|02805|ΚΙΤ ΑΥΞΟΜΕΙΩΣΗΣ ΜΕΓΕΘΟΥΣ ΠΡΟΪΟΝΤΟΣ|1.0|3240.0|2916.0|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|02809|ΚΙΤ ΑΥΞΟΜΕΙΩΣΗΣ ΜΕΓΕΘΟΥΣ ΞΥΛΑΚΙ|1.0|1060.0|954.0|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03824|ΚΑΠΑΚΙ ΦΟΡΜΑΤ 27|2.0|467.0|840.60000000000002|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03872|ΟΔΗΓΟΣ ΦΟΡΜΑΣ Η220 ΓΙΑ SM7000|1.0|1300.0|1170.0|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-01024|30/09/2026|03875|ΑΠΟΣΤΑΤΗΣ PE 20mm|5.0|45.0|202.5|101332.35000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|14/09/2026|03822|BAMBOO SKEWERS PFS LOGO 240*4 PADDLE SSP (5000)|40.0|40.280000000000001|1611.2|1611.2
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|31/08/2026|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|11.0|145.0|1435.5|1435.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00275|31/08/2026|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|14.0|145.0|1827.0|1827.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00275|31/08/2026|03823|ΚΑΠΑΚΙ 21*42|2.0|550.0|0.0|1827.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00275|31/08/2026|03840|ΚΑΠΑΚΙ 21*42 Φ4,5|2.0|550.0|0.0|1827.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|02644|SM 7000 ΑΥΤΟΜΑΤΗ ΣΟΥΒΛΑΚΟΜΗΧΑΝΗ|1.0|154800.0|154800.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|02808|ΞΥΛΟΚΟΥΤΟ ΓΙΑ SM 7000|1.0|1060.0|1060.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|00107|ΚΙΤ ΠΑΡΑΓΩΓΗΣ ΦΟΡΜΑΤ 27|1.0|5255.0|5255.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|02956|ΚΙΒΩΤΙΔΙΟ 21*42 210|5.0|2110.0|10550.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|02821|ΚΙΒΩΤΙΔΙΟ ΦΟΡΜΑΤ 27 210|5.0|1870.0|9350.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|03824|ΚΑΠΑΚΙ ΦΟΡΜΑΤ 27|2.0|477.0|954.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|03823|ΚΑΠΑΚΙ 21*42|2.0|550.0|1100.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|01901|CE CERTIFICATE|1.0|200.0|0.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00241|31/07/2026|03564|ΚIT ΠΑΡΑΓΩΓΗΣ ΦΟΡΜΑΤ 21*42|1.0|6275.0|6275.0|105000.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000205|27/07/2026|03838|BAMBOO SKEWERS 215*3.2 SBP (10000)VN|200.0|24.024999999999999|4324.5|29734.880000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000205|27/07/2026|03829|BAMBOO SKEWERS 215*4 SSP (10000)VN|32.0|24.704999999999998|711.5|29734.880000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000205|27/07/2026|03830|BAMBOO SKEWERS 240*4 SSP (10000)VN|1024.0|26.800000000000001|24698.880000000001|29734.880000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00193|30/06/2026|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|10.0|145.0|1305.0|1305.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|09/06/2026|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|10.0|145.0|1305.0|1305.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00115|30/04/2026|03771|ΒΟΗΘΗΤΙΚΟΣ ΛΑΜΠΤΗΡΑΣ SM7000|1.0|150.0|135.0|1309.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00115|30/04/2026|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|9.0|145.0|1174.5|1309.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|DN00000002|31/03/2026|03766|WOOD SKEWERS 10000PCS Φ3.2L =190 SINGLE BLUNT POINT|1205.0|31.5|37957.5|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|DN00000002|31/03/2026|03765|WOOD SKEWERS 10000 PCS Φ3.7L 160MM ONE BLUNT POINT|1082.0|41.0|44362.0|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΤΕΔΑ-0062|31/03/2026|03766|WOOD SKEWERS 10000PCS Φ3.2L =190 SINGLE BLUNT POINT|1205.0|31.5|37957.5|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΤΕΔΑ-0062|31/03/2026|03765|WOOD SKEWERS 10000 PCS Φ3.7L 160MM ONE BLUNT POINT|1082.0|41.0|44362.0|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00057|17/03/2026|03766|WOOD SKEWERS 10000PCS Φ3.2L =190 SINGLE BLUNT POINT|1205.0|31.5|37957.5|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00057|17/03/2026|03765|WOOD SKEWERS 10000 PCS Φ3.7L 160MM ONE BLUNT POINT|1082.0|41.0|44362.0|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΤΕΔΑ -53|28/02/2026|03748|WOOD SKEWERS O 3.2 L=190 SINGLE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|20.0|3892.0|77840.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΤΕΔΑ -53|28/02/2026|03747|WOOD SKEWERS O 3.7 LENGHT 160mm ONE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|2.0|4397.0|8794.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|03757|SM 7000-PLUS SKEWERING MACHINE WITH GUIDE RAIL|1.0|154800.0|154800.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|02808|ΞΥΛΟΚΟΥΤΟ ΓΙΑ SM 7000|1.0|1060.0|1060.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|03556|PRODUCTION KIT FORMAT 19|1.0|5255.0|5255.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|00069|ΚΙΒΩΤΙΔΙΟ 24 210|5.0|1870.0|9350.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|03742|ΚΙΒΩΤΙΔΙΟ 19 160|5.0|1700.0|8500.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|03641|ΚΑΠΑΚΙ 24 ΜΕ ΦΡΕΖΑ ΕΣΩΤΕΡΙΚΑ 10mm|2.0|477.0|954.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|03743|ΚΑΠΑΚΙ 19|2.0|477.0|954.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|02805|ΚΙΤ ΑΥΞΟΜΕΙΩΣΗΣ ΜΕΓΕΘΟΥΣ ΠΡΟΪΟΝΤΟΣ|1.0|1620.0|1620.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|02809|ΚΙΤ ΑΥΞΟΜΕΙΩΣΗΣ ΜΕΓΕΘΟΥΣ ΞΥΛΑΚΙ|1.0|1060.0|1060.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00045|28/02/2026|02678|ΚΙΤ ΠΑΡΑΓΩΓΗΣ ΦΟΡΜΑΤ 24|1.0|5255.0|5255.0|93213.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΔΑ00000002|27/02/2026|03748|WOOD SKEWERS O 3.2 L=190 SINGLE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|20.0|3892.0|77840.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΔΑ00000002|27/02/2026|03747|WOOD SKEWERS O 3.7 LENGHT 160mm ONE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|2.0|4397.0|8794.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00026|13/02/2026|03748|WOOD SKEWERS O 3.2 L=190 SINGLE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|20.0|3892.0|77840.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00026|13/02/2026|03747|WOOD SKEWERS O 3.7 LENGHT 160mm ONE BLUNT POINTAND MAP PACKAGINGPALLET OF 110 BOXES|2.0|4397.0|8794.0|86634.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00374|22/12/2025|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|15.0|145.0|1957.5|1957.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00268|18/09/2025|02340|ΜΕΤΑΦΟΡΙΚΑ|1.0|60.0|54.0|54.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|18/09/2025|03760|WOOD SKEWERS 160-3.7-SSP-BT|1082.0|41.0|44362.0|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|18/09/2025|03761|WOOD SKEWERS 190-3.2-SSP-BT|1205.0|31.5|37957.5|82319.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000256|10/09/2025|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|8.0|145.0|1044.0|1044.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|08/08/2025|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|8.0|145.0|1044.0|1044.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000178|30/06/2025|03549|ΛΑΜΜΕΣ ΑΥΤΟΜΑΤΗΣ SM7000|15.0|145.0|1957.5|1957.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000178|30/06/2025|03605|ΚΑΡΒΟΥΝΟ ΦΥΣΙΚΟ Α/Α VN 3kg|7.0|8.0|0.0|1957.5
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00102|08/05/2025|03570|ΠΛΑΙΝΟ ΚΙΒΩΤΙΔΙΟΥ 27/210|2.0|145.0|261.0|354.05000000000001
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02778|CUTTING KIT 24/8|1.0|2530.0|1771.0|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02781|CUTTING KIT  27|1.0|2300.0|1610.0|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02787|DRILLING KIT  24|1.0|273.0|191.09999999999999|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02790|DRILLING KIT  27|1.0|273.0|191.09999999999999|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|03547|SENSOR FOR SKEWERING MACHINES IFT203|2.0|79.659999999999997|111.52|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|03547|SENSOR FOR SKEWERING MACHINES IFT203|1.0|79.659999999999997|0.0|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02919|MAGNETIC CYLINDER SENSOR FOR CABLE MT1 GMR, MKT3000-BPKG/1M/ZH/A|2.0|70.019999999999996|98.030000000000001|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|03552|ΚΑΠΑΚΙ 24|1.0|467.0|326.89999999999998|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|02958|ΚΑΠΑΚΙ 27|1.0|467.0|326.89999999999998|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|01924|30 HEIGHT BASIS FOR FORMAT 24 YELLOW|1.0|351.0|315.89999999999998|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|03002|RECOVERY SHIPPING COST AND INSURANCE|1.0|110.0|110.0|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-000046|21/03/2025|03550|ΚΑΤΩ ΠΛΑΚΑ ΠΟΡΤΟΚΑΛΙ 27|1.0|351.0|315.89999999999998|5711.2700000000004
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02778|CUTTING KIT 24/8|1.0|2530.0|1771.0|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02781|CUTTING KIT  27|1.0|2300.0|1610.0|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02787|DRILLING KIT  24|1.0|273.0|191.09999999999999|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02790|DRILLING KIT  27|1.0|273.0|191.09999999999999|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|03547|SENSOR FOR SKEWERING MACHINES IFT203|2.0|79.659999999999997|111.52|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02919|MAGNETIC CYLINDER SENSOR FOR CABLE MT1 GMR, MKT3000-BPKG/1M/ZH/A|2.0|70.019999999999996|98.030000000000001|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|01911|ΚΑΠΑΚΙ ΚΙΤΡΙΝΟ 24 ΕΣ. ΕΞ. ΜΕ ΤΡΥΠΑ 4.2|1.0|467.0|326.89999999999998|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|02958|ΚΑΠΑΚΙ 27|1.0|467.0|326.89999999999998|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|03547|SENSOR FOR SKEWERING MACHINES IFT203|1.0|79.659999999999997|0.0|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΠΑΡ|04/03/2025|03002|RECOVERY SHIPPING COST AND INSURANCE|1.0|110.0|110.0|4736.5500000000002
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|02654|SM 3000 ΑΥΤΟΜΑΤΗ ΣΟΥΒΛΑΚΟΜΗΧΑΝΗ|1.0|60100.0|48080.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|02824|ΚΙΒΩΤΙΔΙΟ  21 WALL 210|3.0|1870.0|4488.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|02818|WOOD BOX FOR PACKAGING MACHINE SM 3000|1.0|790.0|632.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|02675|ΚΙΤ ΠΑΡΑΓΩΓΗΣ ΦΟΡΜΑΤ 21 L140S215Φ3.2|1.0|5255.0|4204.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|01900|SM 3000 MANUAL OF USE AND MAINTENANCE ELECT.AND PNEUMATIC|1.0|161.0|0.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|01901|CE CERTIFICATE|1.0|50.0|0.0|57404.0
12|0133|VN Food Processing Equipment Snc di Vitileia Nicolino & C.|1251|ΤΔΑΕ-00040|29/02/2024|01926|WOOD SKEWERS 200*3.7 SSP (10000)|1.0|110.0|0.0|57404.0
12|0191|EFKA ΙΔΙΩΤΙΚΗ ΚΕΦΑΛΑΙΟΥΧΙΚΗ ΕΤΑΙΡΙΑ|1251|ΤΔΑ-000247|10/02/2025|03036|ΜΑΓΝΗΤΗΣ ΜΑΧΑΙΡΙΩΝ 50εκ.|40.0|3.8799999999999999|155.19999999999999|192.44999999999999
12|0191|EFKA ΙΔΙΩΤΙΚΗ ΚΕΦΑΛΑΙΟΥΧΙΚΗ ΕΤΑΙΡΙΑ|1251|ΤΔΑ-002582|12/11/2024|03036|ΜΑΓΝΗΤΗΣ ΜΑΧΑΙΡΙΩΝ 50εκ.|40.0|3.9399999999999999|157.59999999999999|195.41999999999999
16|0025|ΗΛΙΑΔΗΣ ΚΑΡΓΚΟ Α.Ε|1653|ΤΙΜΔ-ΗΤΠΥΒ02088|19/08/2026|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|1240.0|1537.5999999999999
16|0133|ΠΑΠΑΔΟΠΟΥΛΟΣ  ΠΕΤΡΟΣ ΑΒΡΑΑΜ GADGET STORE|1653|ΤΙΜΔ-B13417|15/04/2024|10043|Αναλώσιμα Επιχείρησης 24%|1.0|0.0|47.479999999999997|58.880000000000003
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0011236|27/07/2026|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|50.0|162.0
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0011236|27/07/2026|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|100.0|162.0
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10887|27/05/2026|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|60.0|74.400000000000006
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10874|27/05/2026|10037|Δαπάνες Εισαγωγών ΤΧ|1.0|0.0|55.0|328.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10874|27/05/2026|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|260.0|328.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10313|05/03/2026|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|60.0|74.400000000000006
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10303|03/03/2026|10037|Δαπάνες Εισαγωγών ΤΧ|1.0|0.0|55.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-10303|03/03/2026|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|180.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0010033|14/01/2026|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|100.0|162.0
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0010033|14/01/2026|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|50.0|162.0
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0009844|05/12/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|60.0|74.400000000000006
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0009843|03/12/2025|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|180.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0009843|03/12/2025|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|55.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0009224|21/08/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|60.0|74.400000000000006
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-009193|13/08/2025|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|180.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-009193|13/08/2025|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|55.0|248.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-08539|30/04/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|60.0|74.400000000000006
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0008504|27/04/2025|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|280.0|348.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0008504|27/04/2025|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|55.0|348.19999999999999
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0008200|17/03/2025|10033|Ναύλος Εισαγωγής 0%|1.0|0.0|150.0|193.40000000000001
16|0191|G T  FAROS ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ|1653|ΤΙΜΔ-0008200|17/03/2025|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|35.0|193.40000000000001
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-00554|28/07/2026|5050|ΦΠΑ εισαγωγών Τρίτων Χωρών|1.0|0.0|282.30000000000001|282.30000000000001
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0074372|28/07/2026|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|50.0|173.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0074372|28/07/2026|10001|Εκτελωνιστικά (Εισαγωγών) 24%|1.0|0.0|90.0|173.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-00526|27/05/2026|10009|ΦΠΑ εισαγωγών Τρίτων Χωρών|1.0|0.0|824.03999999999996|824.03999999999996
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-73793|27/05/2026|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|50.0|173.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-73793|27/05/2026|10001|Εκτελωνιστικά (Εισαγωγών) 24%|1.0|0.0|90.0|173.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-00498|05/03/2026|10009|ΦΠΑ εισαγωγών Τρίτων Χωρών|1.0|0.0|531.60000000000002|531.60000000000002
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-73041|05/03/2026|10034|Πρακτορεικά (Εισαγωγών) 24%|1.0|0.0|45.0|204.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-73041|05/03/2026|10001|Εκτελωνιστικά (Εισαγωγών) 24%|1.0|0.0|120.0|204.59999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0072532|19/01/2026|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|46.0|57.039999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0072222|05/12/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|46.0|57.039999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0071215|21/08/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|46.0|57.039999999999999
16|0212|ΤΖΙΑΣΤΙΔΗΣ  ΓΕΩΡΓΙΟΣ ΧΡΗΣΤΟΣ ΦΑΡΟΣ - ΑΠΟΘΗΚΗ|1653|ΤΙΜΔ-0070286|30/04/2025|81004|Μεταφορικά (Εντός Ελλάδος)|1.0|0.0|47.0|58.280000000000001

(130 rows affected)
```

Note: TOP 400 limit not hit - 130 rows returned.

