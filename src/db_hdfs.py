"""
HDFS Handler for ChurnGuard Platform
Manages data storage and retrieval from Hadoop HDFS
"""
import os
import subprocess
import argparse
from pathlib import Path

# HDFS Configuration
HDFS_NAMENODE = "hdfs://namenode:9000"
HDFS_BASE_PATH = "/churnguard"
HDFS_DATA_PATH = f"{HDFS_BASE_PATH}/data"
HDFS_RAW_PATH = f"{HDFS_BASE_PATH}/data/raw"
HDFS_PROCESSED_PATH = f"{HDFS_BASE_PATH}/data/processed"
HDFS_MODELS_PATH = f"{HDFS_BASE_PATH}/models"

def run_hdfs_command(command):
    """Execute HDFS command via docker exec"""
    try:
        # Use docker exec to run HDFS commands inside namenode container
        docker_cmd = f"docker exec churn-namenode hdfs dfs {command}"
        result = subprocess.run(
            docker_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"✗ HDFS command failed: {e.stderr}")
        return None

def test_connection():
    """Test HDFS connection"""
    print("🔍 Testing HDFS connection...")
    
    try:
        # Check if namenode container is running
        result = subprocess.run(
            "docker ps --filter name=churn-namenode --format '{{.Status}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "Up" not in result.stdout:
            print("✗ Namenode container is not running")
            print("  Run: docker compose up -d namenode datanode")
            return False
        
        # Test HDFS command
        output = run_hdfs_command("-ls /")
        if output is not None:
            print("✓ Connected to HDFS")
            print(f"  Namenode: {HDFS_NAMENODE}")
            return True
        else:
            print("✗ Failed to connect to HDFS")
            return False
            
    except Exception as e:
        print(f"✗ Error testing HDFS: {e}")
        return False

def init_hdfs():
    """Initialize HDFS directory structure"""
    print("📁 Initializing HDFS directory structure...")
    
    directories = [
        HDFS_BASE_PATH,
        HDFS_DATA_PATH,
        HDFS_RAW_PATH,
        HDFS_PROCESSED_PATH,
        HDFS_MODELS_PATH
    ]
    
    for directory in directories:
        result = run_hdfs_command(f"-mkdir -p {directory}")
        if result is not None or "File exists" in str(result):
            print(f"✓ Created/verified: {directory}")
        else:
            print(f"⚠ Could not create: {directory}")
    
    # Set permissions
    run_hdfs_command(f"-chmod -R 777 {HDFS_BASE_PATH}")
    print("✓ HDFS directory structure initialized")

def upload_to_hdfs(local_path, hdfs_path):
    """Upload local file to HDFS"""
    print(f"📤 Uploading {local_path} to HDFS...")
    
    if not os.path.exists(local_path):
        print(f"✗ Local file not found: {local_path}")
        return False
    
    # Use docker cp and then move to HDFS
    try:
        # Copy file to container
        container_path = f"/tmp/{os.path.basename(local_path)}"
        subprocess.run(
            f"docker cp {local_path} churn-namenode:{container_path}",
            shell=True,
            check=True
        )
        
        # Upload to HDFS
        result = run_hdfs_command(f"-put -f {container_path} {hdfs_path}")
        
        if result is not None:
            print(f"✓ Uploaded to: {hdfs_path}")
            return True
        else:
            print(f"✗ Failed to upload to HDFS")
            return False
            
    except Exception as e:
        print(f"✗ Error uploading to HDFS: {e}")
        return False

def download_from_hdfs(hdfs_path, local_path):
    """Download file from HDFS to local"""
    print(f"📥 Downloading {hdfs_path} from HDFS...")
    
    try:
        # Download to container first
        container_path = f"/tmp/{os.path.basename(local_path)}"
        result = run_hdfs_command(f"-get {hdfs_path} {container_path}")
        
        if result is not None:
            # Copy from container to host
            subprocess.run(
                f"docker cp churn-namenode:{container_path} {local_path}",
                shell=True,
                check=True
            )
            print(f"✓ Downloaded to: {local_path}")
            return True
        else:
            print(f"✗ Failed to download from HDFS")
            return False
            
    except Exception as e:
        print(f"✗ Error downloading from HDFS: {e}")
        return False

def list_hdfs(path):
    """List files in HDFS path"""
    print(f"📋 Listing HDFS path: {path}")
    
    result = run_hdfs_command(f"-ls {path}")
    if result:
        print(result)
        return True
    else:
        print(f"✗ Path not found or empty: {path}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HDFS Handler')
    parser.add_argument('--test', action='store_true', help='Test HDFS connection')
    parser.add_argument('--init', action='store_true', help='Initialize HDFS directories')
    parser.add_argument('--upload', nargs=2, metavar=('LOCAL', 'HDFS'), help='Upload file to HDFS')
    parser.add_argument('--download', nargs=2, metavar=('HDFS', 'LOCAL'), help='Download file from HDFS')
    parser.add_argument('--list', type=str, help='List HDFS directory')
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    elif args.init:
        init_hdfs()
    elif args.upload:
        upload_to_hdfs(args.upload[0], args.upload[1])
    elif args.download:
        download_from_hdfs(args.download[0], args.download[1])
    elif args.list:
        list_hdfs(args.list)
    else:
        print("Usage:")
        print("  python src/db_hdfs.py --test")
        print("  python src/db_hdfs.py --init")
        print("  python src/db_hdfs.py --upload <local_path> <hdfs_path>")
        print("  python src/db_hdfs.py --download <hdfs_path> <local_path>")
        print("  python src/db_hdfs.py --list <hdfs_path>")

