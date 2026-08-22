# Chess Bot

> An application for setting a chess board using a robotic arm, or plating chess against it.

---

## Table of Contents

* [Overview](#overview)
* [Requirements](#requirements)
* [Configuration](#configuration)
* [Calibration](#calibration)
* [Running the Project](#running-the-project)
* [Main Flows](#main-flows)
* [Project Structure](#project-structure)
* [Architecture](#architecture)
* [Troubleshooting](#troubleshooting)

---

## Overview

* The project includes two main features performed by the robotic arm:
1. Setting the chess board, from scattered pieces on a cartboard, based on any game position.
2. Playing a chess game against human player (or against itself), starting from any starting game position.
* The features should be run consecutively, but can be ran independently. 
* If the board is not set by the robot, the game starts by either of these methods:
1. The human sets the board, and the app detects the board automatically.
2. The human sets the board, and configures the board position as a FEN string.
- Note: Throughout this document and project we use FEN strings to represents chess boards. 

---

## Requirements

### Hardware

* Computer (CPU is sufficient)
* ZED camera
* UR5E arm
* Chess board, and pieces

### Software

* Python: `[3.13.3]`
* PyTorch: `[2.13.0]`
* Ultralytics: `[8.4.110]`
* python-chess: `[1.11.2]`
* NumPy: `[2.2.4]`
* OpenCV `[4.13.0]`
* ZED SDK `[5.4]`
* Pillow `[11.3.0]`
* torchvision `[0.28.0]`


## Configuration

The configurations of this project affect the game starting position, which player plays each color, how the boards is being set and what parts are handeled manually or automatically (Mocks and Tests)

### Configuration File

The project uses:

```text
[../src/main/config.yaml]
```

An Example of a configutation file can be already found there.

Main settings:

* run_board_setup (bool) - Decides whether the automatic setup by robot runs.
* run_initial_detection(bool) - Decides whether the game initial position is set by the configuration or a detection.
* initial_fen (str) - The FEN string of the game position from which the game starts, also decides the target of automatic setup.
* robot - configuration for using mock or real, speed of the robot and the arm's IP address.
* vision - configuration decides model used during game and whether the detection and classification of pieces during setup are done automaticaly or manually.

---

## Calibration

Before running the chess bot, the camera and robot need to be set and calibrated.

### Physical setup

* The equipment should be put on a flat surface (e.g. a desk) in this order with respect to human's position:
1. Cardboard on which the captured pieces and the pieces to be put on board by the robot should be put.
2. A chess board, next to which a lifted platform for classification and balancing should be put.
3. a ZED camera tilited down towards the surface. 

### Hardware-Software calibration

All the calibration you need to run before first launce are located in this dir:

```text
[../calibration]
```

### Camera-Board Calibration

Run get_board_cornerns.py, an intercative photo of the setup will appear, there you should click 4 points that are coresponding to the cornerns of the chess board. After pressing enter they will be saved in cornerns.json. These are later used to relate detected pieces to squares of the board.

### Robot-Camera Calibration
put text here..................................................
Explain also how coordinates from the camera are transformed into robot coordinates.




---

## Running the Project

### Start the Chess Bot
This command starts the session as configured in the configuration file.

```bash
[python3 -m main.main]
```

## Main Flows

### Game Flow
The Game obects initializes a loop of the chess game itself.
Each iteration the player is selected accordin to turn and the abstract method make_move is called until a chess stop condition is met.

### make_move Flow
For each player make_move() is seperated into two parts:
* HumanPlayer:
1. Plan Move - waits for human reaction.
2. Execute Move - Takes pictures of the board, detect pieces and translates the detections to pieces on board. Comparing the previous and current Board is used to decide the move and update the game Board object.

* RobotPlayer:
1. Plan Move - Using the current board and chess engine chooses a move represented as UCI string (e.g. e4e5).
2. Execute Move - Translates the UCI string into one of 4 move types (Move, Capture, Castle, Upgrade) and executes it using the arm or a mock PlayingRobot.

### Setup Board by Robot Flow
* BoardSetupService initializes a loop of PieceIngestionPipeline process_next_piece until reaches the number of the desired pieces based on the initial FEN configuration.
* process_next_piece is a pipeline composed of these steps:
1. Oreintation Detection - The application takes a picture and cuts it around the cardboards edges. The vision model detects the pieces and predicts their head position, base position and orientation (Lying or Standing). The step ouptus the prediction for the piece most close to the camera.
2. Moving Piece to Platform - Using the outpur for step 1, the arm can pick up a piece and put it vertically on the platform.
3. Classification - While the piece is on the platform the camera takes a picture and crops it around the platform. We proceed to classify the piece to one of 12 chess piece types.
4. Placement Planner - Using the output of step 3 the application computes the target square of the current piece.
5. Move the piece from the platform to the target piece on board (or storage). 

## Project Structure



### `[calibration]/`

Contains file for calibration as introduced in the calibration part.
### `[common]/`

Contains methods and enums used throughtout the whole project.
### `[factories]/`

Contains Factory classes for dependency injection at the start of the sessions. 
### `[runs]/`

Contains the visual models (.pt files) we use for detection.

### `[src]/`

Contains our source code for the chess logic and flows as described in Main Flows.
```text

├── src/
│   ├── arm
│   ├── core_functionalities
│   ├── main
│   └── perception
```
* arm -Contains all the files and classes with arm functionality inclduing: PlatingRobot, SettingRobot, RobotHardware (direct movement methods).
* core_functionalities - Contains game main flows code and the chess engine classes.
* main - Contains configuration classes, sesseion class to load configuration with factories, and main file to run the sessions.
* perception - important subdirs: vision_inference handle vision models inference; processing handle the processing of pure detections. ZED - handles camera functionalities. 

### `[tests]/`

Contains test scripts we used for checking each compoonent separetly.

---

## Architecture

A full diagram of the classes desgin and architecture can be find in the attached architecture.docx


---

## Troubleshooting

### `[Problem 1]`

**Problem:**

The full class detection model we achieved makes mistakes. It is not reliable enough for using every turn.
**Solution:**

1. We added a binary model that can distinguish only between colors. For comparing two boards and one move it's mostly enough.
2. We added optimization to the YOLO classifier that changes classes to detected pieces until a legal board is achieved. Used mostly when detecting the initial board where the binary model cannot be used.
---

### `[Problem 2]`

**Problem:**

During a game large pieces can block pawns, the model fails to detect them. 
**Solution:**

We can almost always detect the exact move even if the pawn is blocked because those cases are disjoint assuming the players make only legal moves. The application prints a message whenever a pawn is blocked.
However, if the block is not dealt with, it can move to the next turn and there will be unrecognizable, since our implementation can only catch blocking due to current move.
---

### `[Problem 3]`

**Problem:**

Sometimes the arm fails to grab a piece from cardboard, and the classifier outputs a piece even if the platform is empty.
**Solution:**

We noticed that in all this cases the difference in vonfidence was very high, so we added a behavior according to which: if the confidence of classifier is low, then we continue picking up new piece since it is likely never made it to the platform.
---
