FROM python:3.9.9-slim-buster

#https://github.com/pythonnet/pythonnet/issues/1346#issuecomment-1101332342

RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

# .NET Core sources
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb

# Mono and .NET
RUN apt update \
    && apt install -y apt-transport-https dirmngr gnupg \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/debian stable-buster main" \
    | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt update \
    && apt-get install -y clang mono-complete \
        dotnet-sdk-6.0 \
        libglib2.0 g++ \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Install any Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Install Git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Clone repositories
RUN git clone https://github.com/thermofisherlsms/RawFileReader.git /RawFileReader \
    && git clone https://github.com/mtinti/raw_qc.git /raw_qc

# Set the working directory
WORKDIR /data

# Set the entry point to run your script
ENTRYPOINT ["python3", "/raw_qc/make_qc.py"]