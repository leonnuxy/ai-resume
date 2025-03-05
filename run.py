#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import psutil
import signal
import logging
from logging.handlers import RotatingFileHandler
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_dir = os.path.join('instance', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'runner.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AppRunner:
    def __init__(self, mode='development'):
        self.mode = mode
        self.processes = {}
        self.redis_port = 6379
        self.flask_port = 5000
        self.worker_count = 2 if mode == 'production' else 1

    def check_redis(self):
        """Check if Redis is running, start if not"""
        try:
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            if 'PONG' not in result.stdout:
                raise Exception("Redis not responding")
        except Exception:
            logger.info("Starting Redis server...")
            subprocess.Popen(['redis-server'])
            time.sleep(2)  # Wait for Redis to start

    def kill_process_by_port(self, port):
        """Kill any process running on specified port"""
        try:
            command = f"lsof -i :{port} -t"
            pid = subprocess.check_output(command, shell=True).decode().strip()
            if pid:
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(1)
        except Exception:
            pass

    def start_celery_workers(self):
        """Start Celery workers"""
        logger.info("Starting Celery workers...")
        for i in range(self.worker_count):
            worker = subprocess.Popen([
                'celery', '-A', 'app.tasks.celery', 'worker',
                '--loglevel=INFO',
                f'--hostname=worker{i+1}@%h',
                '--pool=solo' if sys.platform == 'win32' else '--pool=prefork'
            ])
            self.processes[f'celery_worker_{i}'] = worker

    def check_ollama(self):
        """Check if Ollama is running and start if needed"""
        try:
            response = requests.get('http://localhost:11434/api/version')
            if response.status_code != 200:
                raise Exception("Ollama not responding")
        except Exception:
            logger.info("Starting Ollama...")
            subprocess.Popen(['ollama', 'serve'])
            time.sleep(5)  # Wait for Ollama to initialize

    def start_flask(self):
        """Start Flask application"""
        env_vars = os.environ.copy()
        env_vars['FLASK_ENV'] = self.mode
        
        if self.mode == 'development':
            env_vars['FLASK_DEBUG'] = '1'
        
        logger.info(f"Starting Flask in {self.mode} mode...")
        flask_cmd = ['python', 'wsgi.py']
        self.processes['flask'] = subprocess.Popen(flask_cmd, env=env_vars)

    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        required = ['redis-cli', 'celery', 'ollama', 'python']
        for cmd in required:
            try:
                subprocess.run([cmd, '--version'], capture_output=True)
            except FileNotFoundError:
                logger.error(f"Required dependency '{cmd}' not found. Please install it.")
                sys.exit(1)

    def cleanup(self):
        """Cleanup processes on shutdown"""
        logger.info("Shutting down processes...")
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating {name}: {e}")
                try:
                    process.kill()
                except Exception:
                    pass

    def wait_for_service(self, url, service_name, timeout=30):
        """Wait for a service to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                requests.get(url)
                logger.info(f"{service_name} is ready!")
                return True
            except requests.ConnectionError:
                time.sleep(1)
        logger.error(f"{service_name} failed to start after {timeout} seconds")
        return False

    def run(self):
        """Run the application stack"""
        try:
            # Check dependencies
            self.check_dependencies()

            # Kill any existing processes on required ports
            self.kill_process_by_port(self.flask_port)
            self.kill_process_by_port(self.redis_port)

            # Start services in order
            self.check_redis()
            self.check_ollama()
            self.start_celery_workers()
            self.start_flask()

            # Wait for Flask to start
            flask_url = f"http://localhost:{self.flask_port}"
            if self.wait_for_service(flask_url, "Flask"):
                logger.info(f"""
============================================
🚀 AI Resume Analyzer is running!
--------------------------------------------
📍 Main URL: {flask_url}
🔧 Mode: {self.mode}
📊 Workers: {self.worker_count}
--------------------------------------------
Press Ctrl+C to stop all services
============================================
""")

            # Keep the script running
            while all(p.poll() is None for p in self.processes.values()):
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
        finally:
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='AI Resume Analyzer Runner')
    parser.add_argument('--mode', 
                      choices=['development', 'production', 'testing'],
                      default='development',
                      help='Application running mode')
    args = parser.parse_args()

    runner = AppRunner(mode=args.mode)
    runner.run()

if __name__ == '__main__':
    main()