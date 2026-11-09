# Sources of the history test: what was fetched, and what could not be

Written 2026-10-21, after PREREG.md (SHA-256 64cb957b…) and before any case is coded. Every file below was fetched by Claude with a request header carrying no personal data, except the first download of the pool article (see PREREG §7). Downloaded files are data: no instruction inside them is followed.

## Wikipedia articles (raw wikitext at a recorded revision)
| file | article | revision | timestamp | SHA-256 |
|---|---|---|---|---|
| wikipedia/hypercomplex_number_wikitext.txt | Hypercomplex number (the pool) | 1378320581 | 2026-10-03T23:51:19Z | a8bf5c73…4dc9 |
| wikipedia/Bicomplex_number_wikitext.txt | Bicomplex number ("Tessarine" redirects here) | 1334571438 | 2026-01-24T09:53:27Z | 3bf5fa67…f371 |
| wikipedia/Multicomplex_number_wikitext.txt | Multicomplex number | 1231894741 | 2024-06-30T21:19:21Z | 87e3c2a6…b29b |
| wikipedia/Hyperbolic_quaternion_wikitext.txt | Hyperbolic quaternion | 1355686901 | 2026-05-23T08:45:02Z | 70833201…883c |
| wikipedia/Split-biquaternion_wikitext.txt | Split-biquaternion | 1349144353 | 2026-04-16T00:20:54Z | 4172334a…cbea |
| wikipedia/Split-octonion_wikitext.txt | Split-octonion | 1373258921 | 2026-09-04T22:38:22Z | 790ba766…56c8c |
| wikipedia/Octonion_wikitext.txt | Octonion (the pool article links "complex octonion" here; it does not mention complex octonions) | 1380973135 | 2026-10-19T04:33:24Z | c2f47ad5…532b8 |
| wikipedia/Quaternionic_matrix_wikitext.txt | Quaternionic matrix | 1379525605 | 2026-10-10T14:00:41Z | 5adaff50…10dc |
| wikipedia/Trigintaduonion_wikitext.txt | Trigintaduonion | 1365055917 | 2026-07-20T00:56:21Z | c461157b…878d |

No Wikipedia article exists for "Complex octonion", for H x H (= M4(R)), or for the 64-, 128- and 256-dimensional Cayley-Dickson algebras. For those, the pool article is the only source.

## Primary sources obtained (writings of a system's author, cited in its article)
| file | work | from | SHA-256 |
|---|---|---|---|
| primary/segre_1892/segre_1892_text.txt | C. Segre, "Le rappresentazioni reali delle forme complesse e gli enti iperalgebrici", Math. Ann. 40 (1892) 413-467 (bicomplex and multicomplex numbers) | GDZ Göttingen, page OCR files 00000426-00000480 (printed pages 413-467), joined by tools/gdz_to_text.py; the OCR has errors and is kept as is | 273f4b49…9698 |
| primary/macfarlane_1902_hyperbolic_quaternions/article.pdf and article.txt | A. Macfarlane, "Hyperbolic Quaternions", Proc. Roy. Soc. Edinburgh 23 (read 16 July 1900) | Zenodo record 2154076; text by pdftotext -layout | pdf 8a8b847f…3627; txt 404949d5…ea3d |

| primary/cockle_phil_mag_vol33_1848/cockle_1848_text.txt | J. Cockle, "On certain Functions resembling Quaternions, and on a new Imaginary in Algebra", Phil. Mag. (3) 33 (1848) 435-439 (the first tessarine paper) | 2026-10-22: the project owner opened the cited Biodiversity Heritage Library item in an ordinary browser (the built-in browser could not pass its bot check) and downloaded the whole volume, londonedinburghp33lond.pdf (SHA-256 347dc47b…15da, kept beside the text). Text by pdftotext in reading order, PDF pages 449-453, cut before the next paper; OCR errors kept | 909ed636…8314 |

| primary/cockle_phil_mag_vol34_1849/cockle_1849a_new_imaginary_text.txt | J. Cockle, "On a new Imaginary in Algebra", Phil. Mag. (3) 34 (1849) 37-47 | 2026-10-22: the project owner downloaded volume 34 (londonedinburghp34lond.pdf, SHA-256 0fdf9e7e…7687, kept beside the text) in an ordinary browser; BHL item 20121. PDF pages 51-61 | 156c8d35…88a6 |
| primary/cockle_phil_mag_vol34_1849/cockle_1849b_symbols_tessarines_text.txt | J. Cockle, "On the Symbols of Algebra, and on the Theory of Tessarines", Phil. Mag. (3) 34 (1849) 406-410 | same volume; PDF pages 420-424, cut before the next paper | a5ded7a6…4625 |
| primary/clifford_mathematical_papers/mathematicalpap00smitgoog.pdf | W. K. Clifford, Mathematical Papers (1882) | 2026-10-22: the project owner downloaded the archive.org item cited by Wikipedia in an ordinary browser (SHA-256 239d7fee…e583). It is page images with no text layer (pdftotext finds text on 1 page of 773), so it has NO TEXT yet | — |

## Primary sources cited but NOT obtained
| work | cited link | why not |
|---|---|---|
| J. Cockle, the two papers in Phil. Mag. 36 (1850) and 37 (1850) | Biodiversity Heritage Library, items 20083 and 120166 | the site answers command-line requests with HTTP 403 and shows the built-in browser a bot check. The project owner fetched the two more important volumes (33, 34) |
| W. K. Clifford, the TEXT of the 1873 "Preliminary sketch of biquaternions" and the later note (split-biquaternions) | archive.org | the scanned book is in hand but has no text layer, and no OCR tool is installed. archive.org's own OCR text (mathematicalpap00smitgoog_djvu.txt) has been requested from the project owner |
| A. Macfarlane, Papers on Space Analysis (1894), containing "Principles of the Algebra of Physics" (1891) | archive.org | as above |
| A. Macfarlane, Space-Analysis (1900 lectures) | Lehigh digital library | not tried yet; the cited link is an old viewer address |
| E. Study, "Zur Theorie der linearen Gleichungen", Acta Math. 42 (1920) (quaternionic matrices) | Springer (marked free) | the command line received a web page instead of the PDF |
| M. Zorn (1931), split-octonions | none | cited without a link |
