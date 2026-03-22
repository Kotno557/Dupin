# Use an official Ubuntu image as a base
FROM ubuntu:latest

# Set environment variables for non-interactive apt commands
ENV DEBIAN_FRONTEND=noninteractive

# Update apt and install system dependencies
RUN apt update && apt install -y \
    python3-pip \
    dublin-traceroute \
    nmap \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
# Copy the rest of the application files
COPY dupin_server.py .
COPY dupin_vpn_server.py .
COPY default-config-file/ default-config-file/
COPY lib/dupin_python_lib/ lib/dupin_python_lib/

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI application
# Assuming dupin_server.py is the FastAPI app and it might use dupin_vpn_server.py internally
CMD ["uvicorn", "dupin_server:app", "--host", "0.0.0.0", "--port", "8000"]
