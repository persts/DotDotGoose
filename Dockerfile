# Stolen from https://github.com/dasycarpum/docker-pyqt6/blob/main/docker/Dockerfile

# Use Ubuntu as the base image
FROM ubuntu:23.10

# Combine ENV statements
ENV DEBIAN_FRONTEND=noninteractive \
    LIBGL_ALWAYS_INDIRECT=1 \
    QT_DEBUG_PLUGINS=1 \
    QT_QUICK_BACKEND=software

# Add user
RUN apt-get update && apt-get install -y adduser \
    && adduser --quiet --disabled-password --gecos '' qtuser \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Python 3 and PyQt6
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-dev \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-render0 \
    libxcb-glx0 \
    libxi6 \
    libxkbfile1 \
    libxcb-cursor0 \
    # For QtWebEngine
    libqt5webenginecore5 \
    libqt5webchannel5 \
    qtwebengine5-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the application code into the container
COPY ./ ./

# Set the main script as the container's entrypoint
CMD ["python3", "./main.py"]

# docker build -t dotdotgoose .
# xhost +
# docker run --rm -it \
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     -v $HOME:$HOME \
#     -e PYTHONPATH=/usr/src/app \
#     -e DISPLAY=$DISPLAY \
#     -e QT_QPA_PLATFORM=xcb \
#     --user $(id -u):$(id -g) \
#     dotdotgoose
# xhost -

