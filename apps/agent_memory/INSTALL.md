# Installing Memori

## Installation Options

### Option 1: User Installation (Recommended for macOS)

```bash
python3 -m pip install --user memori
```

### Option 2: Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install Memori
pip install memori
```

### Option 3: System-wide (Not Recommended)

```bash
python3 -m pip install --break-system-packages memori
```

## Verify Installation

```bash
python3 -c "import memori; print('Memori installed:', memori.__version__)"
```

## Next Steps

After installation, run the setup script:

```bash
python3 apps/agent_memory/setup.py
```

Or test the installation:

```bash
python3 apps/agent_memory/test_memori.py
```

