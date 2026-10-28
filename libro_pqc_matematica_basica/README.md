# El Secreto de los Retículos: Una Aventura Visual e Intuitiva por la Criptografía Post-Cuántica

> **Nivel:** Primer semestre de Matemática Básica / Álgebra Lineal / Informática  
> **Institución:** Universidad Mayor de San Andrés (UMSA) — Facultad de Ciencias Puras y Naturales  
> **Compilador:** LaTeX (`pdflatex`) | **Documento Principal:** `main.tex`  
> **PDF Compilado:** `main.pdf` (27 páginas, 592 KB)

---

## 🎯 Objetivo Pedagógico

Explicar las **Primitivas Criptográficas Post-Cuánticas (PQC)** de la forma más comprensible, visual e intuitiva posible, omitiendo las complejidades de la criptografía clásica y apoyándose únicamente en:
- Geometría de cuadrículas en el plano cartesiano (retículos 2D).
- La aritmética del reloj (aritmética modular $\mathbb{Z}_q$).
- El álgebra elemental de polinomios ($x^n = -1$).
- Metáforas cotidianas (mezcla de pinturas, susurros en conciertos, arqueros que abortan disparos).

---

## 📚 Estructura de Capítulos

| Archivo | Título del Capítulo | Conceptos Clave Introducidos |
|---|---|---|
| `capitulos/prologo.tex` | **Prólogo: Para el Estudiante Curioso** | Motivación, el candado del futuro y mapa de ruta. |
| `capitulos/cap1_el_arte_del_secreto.tex` | **Capítulo 1: La Pregunta Fundamental** | Funciones trampa, el fallo de Gauss ante ecuaciones ruidosas. |
| `capitulos/cap2_reticulos_geometria.tex` | **Capítulo 2: Una Cuadrícula Infinita en el Espacio** | Retículos (*lattices*), base buena vs. base mala, problema CVP. |
| `capitulos/cap3_lwe_el_ruido_salvador.tex` | **Capítulo 3: El Secreto con Ruido (LWE)** | Aritmética modular $\mathbb{Z}_q$, el problema LWE de Regev, ejemplo numérico. |
| `capitulos/cap4_polinomios_y_modulos.tex` | **Capítulo 4: De Números Sueltos a Polinomios** | Anillo $R_q$, carrusel $x^n=-1$, módulos, Module-LWE (M-LWE). |
| `capitulos/cap5_mlkem_el_candado.tex` | **Capítulo 5: El Candado Post-Cuántico (ML-KEM)** | KEM, cancelación algebraica de matrices, redondeo $0$ vs $q/2$. |
| `capitulos/cap6_mldsa_el_sello.tex` | **Capítulo 6: El Sello Incorruptible (ML-DSA)** | Firmas digitales, Module-SIS, muestreo con rechazo de Lyubashevsky. |
| `capitulos/cap7_epilogo_y_glosario.tex` | **Capítulo 7: Epílogo y Glosario Amigable** | Resumen conceptual, conexión con el proyecto UMSA y glosario. |

---

## 🛠️ Cómo Recompilar

Desde la terminal en esta carpeta:
```bash
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
