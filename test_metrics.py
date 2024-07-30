import psutil

# Get memory details
memory_info = psutil.virtual_memory()

# Free memory
free_memory = memory_info.free

# Print free memory in bytes
print(f"Free memory: {free_memory} bytes")

# Optionally, print free memory in a more human-readable format (e.g., MB or GB)
free_memory_mb = free_memory / (1024 ** 2)
free_memory_gb = free_memory / (1024 ** 3)
print(f"Free memory: {free_memory_mb:.2f} MB")
print(f"Free memory: {free_memory_gb:.2f} GB")

# Get disk usage details for the root partition
disk_usage = psutil.disk_usage('/')

# Free storage
free_storage = disk_usage.free

# Print free storage in bytes
print(f"Free storage: {free_storage} bytes")

# Optionally, print free storage in a more human-readable format (e.g., MB or GB)
free_storage_mb = free_storage / (1024 ** 2)
free_storage_gb = free_storage / (1024 ** 3)
print(f"Free storage: {free_storage_mb:.2f} MB")
print(f"Free storage: {free_storage_gb:.2f} GB")
