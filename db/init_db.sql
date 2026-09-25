DROP DATABASE IF EXISTS club_deportivo;
CREATE DATABASE club_deportivo;
USE club_deportivo;

CREATE TABLE deportes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE canchas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    id_deporte INT NOT NULL,
    precio_hora INT NOT NULL CHECK (precio_hora > 0),
    techada BOOLEAN DEFAULT FALSE,
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_deporte) REFERENCES deportes(id)
);

CREATE TABLE socios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_socio INT NOT NULL,
    id_cancha INT NOT NULL,
    fecha_hora_inicio DATETIME(6) NOT NULL,
    fecha_hora_fin DATETIME(6) NOT NULL,
    estado ENUM('confirmada', 'cancelada', 'finalizada') DEFAULT 'confirmada',
    tarifa_historica INT NOT NULL,
    total INT NOT NULL,
    FOREIGN KEY (id_socio) REFERENCES socios(id),
    FOREIGN KEY (id_cancha) REFERENCES canchas(id),
    CHECK (fecha_hora_inicio < fecha_hora_fin)
);

-- Datos de prueba
INSERT INTO deportes (nombre) VALUES 
('Fútbol'), 
('Tenis');

INSERT INTO canchas (nombre, id_deporte, precio_hora, techada, activa) VALUES 
('Cancha 1 - Fútbol 5', 1, 1000000, FALSE, TRUE),
('Cancha Central - Tenis', 2, 1500000, TRUE, TRUE);

INSERT INTO socios (nombre, email, activo) VALUES 
('pepe', 'pepe@ejemplo.com', TRUE),
('ana', 'ana@ejemplo.com', TRUE);

INSERT INTO reservas (id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin, estado, tarifa_historica, total) VALUES 
(1, 1, '2026-10-15 18:00:00.000000', '2026-10-15 20:00:00.000000', 'confirmada', 1000000, 2000000);