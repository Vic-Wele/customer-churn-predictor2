"""
HDFS Data Ingestion Script for ChurnGuard Platform
Uploads raw data files to Hadoop HDFS for distributed storage
"""
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# HDFS Configuration
HDFS_NAMENODE = "hdfs://namenode:9000"
HDFS_RAW_PATH = f"{HDFS_NAMENODE}/churnguard/data/raw"

def run_hdfs_command(command):
    """Execute HDFS command via docker exec"""
    try:
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

def upload_file_to_hdfs(local_path, hdfs_filename=None):
    """Upload a local file to HDFS"""
    if not os.path.exists(local_path):
        print(f"✗ Local file not found: {local_path}")
        return False
    
    if hdfs_filename is None:
        hdfs_filename = os.path.basename(local_path)
    
    hdfs_path = f"{HDFS_RAW_PATH}/{hdfs_filename}"
    
    print(f"📤 Uploading {local_path} to HDFS...")
    
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
        
        if result is not None or "File exists" in str(result):
            print(f"✓ Uploaded to HDFS: {hdfs_path}")
            
            # Verify upload
            verify_result = run_hdfs_command(f"-ls {hdfs_path}")
            if verify_result:
                print(f"✓ Verified: File exists in HDFS")
                return True
            else:
                print(f"⚠ Upload may have failed - file not found in HDFS")
                return False
        else:
            print(f"✗ Failed to upload to HDFS")
            return False
            
    except Exception as e:
        print(f"✗ Error uploading to HDFS: {e}")
        return False

def upload_dataset():
    """Upload the main telco churn dataset to HDFS"""
    print("=" * 60)
    print("🚀 HDFS DATA INGESTION")
    print("=" * 60)
    
    # Check if namenode is running
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
    
    # Upload telco churn dataset
    dataset_path = "data/raw/telco_churn.csv"
    
    if not os.path.exists(dataset_path):
        print(f"✗ Dataset not found: {dataset_path}")
        print("  Please download the dataset first:")
        print("  wget -O data/raw/telco_churn.csv https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv")
        return False
    
    success = upload_file_to_hdfs(dataset_path, "telco_churn.csv")
    
    if success:
        print("\n" + "=" * 60)
        print("✅ HDFS INGESTION COMPLETE!")
        print(f"   Dataset available at: {HDFS_RAW_PATH}/telco_churn.csv")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ HDFS INGESTION FAILED")
        print("=" * 60)
        return False

def list_hdfs_files():
    """List files in HDFS raw directory"""
    print(f"📋 Listing files in HDFS: {HDFS_RAW_PATH}")
    
    result = run_hdfs_command(f"-ls {HDFS_RAW_PATH}")
    if result:
        print(result)
        return True
    else:
        print(f"✗ Directory not found or empty: {HDFS_RAW_PATH}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HDFS Data Ingestion')
    parser.add_argument('--upload', action='store_true', help='Upload dataset to HDFS')
    parser.add_argument('--list', action='store_true', help='List files in HDFS')
    parser.add_argument('--file', type=str, help='Upload specific file to HDFS')
    
    args = parser.parse_args()
    
    if args.upload:
        upload_dataset()
    elif args.list:
        list_hdfs_files()
    elif args.file:
        upload_file_to_hdfs(args.file)
    else:
        print("Usage:")
        print("  python src/ingest_hdfs.py --upload    # Upload main dataset")
        print("  python src/ingest_hdfs.py --list      # List HDFS files")
        print("  python src/ingest_hdfs.py --file <path>  # Upload specific file")

