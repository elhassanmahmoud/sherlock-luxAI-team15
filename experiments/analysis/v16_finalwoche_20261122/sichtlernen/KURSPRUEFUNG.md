# Der Erkundungsberater im Kursrunner

Die separate Forschungs-ZIP enthält V16 und die aus Sichtgewinnen erlernten 13 Koeffizienten mit ihrem Achsenabschnitt. Die originalen V16-Gewichte sind bytegleich. Auf Python 3.10 und Python 3.13 reproduzierte das entpackte Paket alle **19.392 einzelnen Einheitenbefehle** aus vier vollständigen Spielen gegen Solution und den Kaggle-Dritten. In den vier Referenzpartien änderte der Berater 17 bis 20 Züge. [Paketbau](paket.py) · [Python 3.10](kurs310.json) · [Python 3.13](kurs313.json)

Im unveränderten Kursrunner stimmten außerdem die jeweils 4.848 Einheitenbefehle zweier Solution-Spiele mit den tatsächlich gemessenen Forschungsbefehlen überein, auf Startseite 0 mit ausgeschaltetem Training und auf Startseite 1 trotz 303 Update-Aufrufen und einem Speicheraufruf. Die Gewichtsdatei blieb bytegleich. SHA-256 des Forschungspakets `45970b09f22c5312ceda84d8bfb74ad50d5d2ca72223e5a37879a5892d08dc50`. [Sitz 0](kurslauf_p0.json) · [Sitz 1](kurslauf_p1.json)

Die separate Variante im Ordnerformat `Gruppe15` lud unter Python 3.10 im Projektordner sowie unter `agents/`. Der Kursrunner reproduzierte damit die beiden aufgezeichneten Solution-Spiele auf beiden Sitzplätzen. SHA-256 `1a246ba2999820af867b788f9804f2d0aab98cce2ff5c77d96114eddda35d85d`. [P0](battle_p0.json) · [P1](battle_p1.json)
