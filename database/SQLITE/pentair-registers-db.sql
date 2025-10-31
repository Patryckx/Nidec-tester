--
-- File generated with SQLiteStudio v3.4.17 on jue. oct. 30 21:00:59 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: pentair-tester-registers
CREATE TABLE IF NOT EXISTS "pentair-tester-registers" (id INTEGER PRIMARY KEY AUTOINCREMENT, "id-prueba" INTEGER NOT NULL, "id-pieza-ok" INTEGER NOT NULL, "id-pieza-ng" INTEGER NOT NULL, "numero-empleado" TEXT NOT NULL, "numero-orden" TEXT NOT NULL, "codigo-serial" TEXT NOT NULL, "codigo-qr" TEXT NOT NULL, "version-firmware" TEXT NOT NULL, "comunicacion-232" TEXT NOT NULL, "prueba-leds" TEXT NOT NULL, "prueba-lcds" TEXT NOT NULL, "prueba-botones" TEXT NOT NULL, "prueba-entradas-digitales" TEXT NOT NULL, fecha NUMERIC NOT NULL DEFAULT (CURRENT_TIMESTAMP));

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
