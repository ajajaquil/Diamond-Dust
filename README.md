<div align="center">

# 💍 Diamond Dust

A diamond ring drawn out of ASCII characters and sparkles, spinning in its own pop-up window.

Hi, I'm Aquil. This is a creative-coding project I built for fun,<br>and it is also a place where I practised 3D math and vectorised NumPy.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Math-013243?logo=numpy&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-Window-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## 📌 Overview

`art.py` builds a 3D ring (a torus band, four prongs and a faceted diamond) out of thousands of points, lights them, and renders every frame as ASCII characters on a black canvas. The ring draws itself from the bottom up, then turns slowly while light sparkles off the stone. Under the animation, a live code panel types out the source code that makes it.

When you run it, a **new window pops up**, just like any GUI program.

---

## ✨ Features

- Ring that draws itself from the band, to the prongs, to the diamond
- Flat-shaded diamond facets that catch the light
- Key light, a moving rim light and a specular highlight
- ASCII rendering with a per-cell depth buffer
- Four-ray sparkle flares and a bigger flare on top of the stone
- Orbiting dust trails and twinkling background specks
- Live footer with rotation angle, glint count and letter count
- Code panel that types the source, starting from the function that builds the ring
- Resizable window, closes with `Esc` or `Q`

---

## 🛠 Technology Stack

| Category | Tools |
|---|---|
| Language | Python |
| Math | NumPy |
| Window and drawing | Pygame |
| Standard library | os, re, sys, time, bisect, keyword |

---

## 📁 Project Structure

```
.
├── art.py
├── README.md
└── LICENSE
```

---

## 🔄 Rendering Workflow

```
Ring geometry (points + normals)
        ↓
Draw sweep (what is visible at time t)
        ↓
Rotation around the Y axis
        ↓
Lighting (key + rim + specular)
        ↓
Projection to the screen
        ↓
Depth buffer (nearest point per ASCII cell)
        ↓
Pick a character by brightness
        ↓
Sparkle flares + orbit dust
        ↓
Footer, status bar and code panel
```

---

## ⚙️ How It Works

1. The band is a torus, the prongs are four thin tubes, and the diamond is built from flat triangular facets. Each facet has its own normal, which is what makes it sparkle.
2. Every point gets a draw order, so the ring appears from the bottom of the band up to the tip of the diamond.
3. After the sweep finishes, the whole ring rotates around the Y axis.
4. Each point is lit by a key light, a moving rim light and a specular term.
5. Points are projected to the screen and grouped into small cells. Only the nearest point in each cell is kept.
6. Each cell shows one character from ` .,-~:;=!*#$@`, chosen by its brightness.
7. Bright facets get star-shaped flares, and dust particles orbit the ring.
8. The code panel types out `art.py` itself, starting from `def band():`.

---

## 📚 Learning Outcomes

- Building 3D shapes from points and normals
- Vectorising geometry and lighting with NumPy
- Depth buffering without a graphics library
- Drawing and timing animations in Pygame
- Keeping a frame loop smooth at 60 FPS

---

## ⚠️ Current Limitations

- Needs a screen, so it will not run on a headless server
- The layout is tuned for a portrait canvas of 478 × 850
- Looks best with a monospace font such as Consolas
- Everything is computed on the CPU

---

## 🚀 Future Improvements

- Command-line options for size, speed and text
- Save the animation as a video or GIF
- Other shapes besides the ring
- Colour themes
- Sound

---

## 📝 Repository Note

This repository is a record of something I made for the joy of it. It is not a polished library, and I plan to keep improving it.

---

## 📦 Requirements

You need **Python 3.9 or newer** and two libraries that are not part of Python:

| Library | Why |
|---|---|
| `numpy` | all of the 3D math |
| `pygame` | the pop-up window and drawing |

Everything else is built into Python, so there is nothing more to install.

---

## ▶️ Run It Straight From This Repo

You do not need to download or copy the code by hand. Clone the repository and run it:

```bash
git clone https://github.com/ajajaquil/Diamond-Dust.git
cd Diamond-Dust
pip install -r requirements.txt
python art.py
```

If `pip` is not found, use `python -m pip install -r requirements.txt` instead.

A window opens and the ring starts drawing itself. Press `Esc` or `Q` to close it.

Prefer to keep your system clean? Use a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python art.py
```

---

## 👤 Author

**Ajaj Mahmud Aquil**
Web Developer

- Portfolio: [portfolio.ajajaquil.dev](https://portfolio.ajajaquil.dev)
- GitHub: [!ajajaquil](https://github.com/ajajaquil)
- LinkedIn: [@ajajmahmudaquil](https://www.linkedin.com/in/ajajmahmudaquil)

---

## 📄 License

This project is licensed under the MIT License.