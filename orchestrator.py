"""
uStore to MDSF Migration Pipeline
Master orchestrator that runs all migration steps in sequence
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

class MigrationPipeline:
    def __init__(self, config_file='pipeline_config.json'):
        """Initialize the migration pipeline with configuration"""
        self.config = self.load_config(config_file)
        self.project_dir = Path(__file__).parent.parent
        self.scripts_dir = self.project_dir / 'scripts'
        self.log_file = self.project_dir / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Track pipeline state
        self.state = {
            'current_step': 0,
            'completed_steps': [],
            'failed_steps': [],
            'start_time': None,
            'end_time': None
        }
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        config_path = Path(config_file)
        
        # Default configuration
        default_config = {
            "store_id": 70,
            "store_name": "AFC Urgent Care",
            "use_auto_thumbnail": True,
            "test_mode": False,
            "test_product_limit": 1,
            
            "paths": {
                "assets_dir": "static_assets",
                "thumbnails_dir": "static_assets_thumbnails",
                "output_dir": "../output"
            },
            
            "database": {
                "server": "SIS-SQL\\XMPIE",
                "database": "uStore",
                "user": "XMPieUStore",
                "password": "uStore1"
            },
            
            "steps": {
                "filter": {
                    "enabled": True,
                    "script": "store_filter.py",
                    "input": "uStore_Complete_Export.csv",
                    "output": "Store_Export.csv"
                },
                "seo_generation": {
                    "enabled": True,
                    "script": "SEO_generator.py",
                    "output": "with_seo.csv"
                },
                "asset_linking": {
                    "enabled": True,
                    "script": "asset_linker.py",
                    "output": "with_assets.csv"
                },
                "mdsf_mapping": {
                    "enabled": True,
                    "script": "fields_mapper.py",
                    "output": "mdsf_import.csv"
                },
                "packaging": {
                    "enabled": True,
                    "script": "packager.py",
                    "output": "MDSF_Import_Package.zip"
                }
            }
        }
        
        # Load from file if exists, otherwise use defaults
        if config_path.exists():
            print(f"Loading configuration from: {config_path}")
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults (loaded config takes precedence)
                default_config.update(loaded_config)
        else:
            print(f"Configuration file not found: {config_path}")
            print("Using default configuration")
            print("Creating default config file...")
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Config saved to: {config_path}")
        
        return default_config
    
    def log(self, message, level="INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def print_banner(self, text):
        """Print a formatted banner"""
        banner = "=" * 80
        print(f"\n{banner}")
        print(f"{text:^80}")
        print(f"{banner}\n")
    
    def run_python_script(self, script_name, args=None):
        """Execute a Python script"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        self.log(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.scripts_dir)
        )
        
        # Log output
        if result.stdout:
            self.log(result.stdout, "OUTPUT")
        if result.stderr:
            self.log(result.stderr, "ERROR")
        
        if result.returncode != 0:
            raise Exception(f"Script failed with return code {result.returncode}")
        
        return result
    
    def run_powershell_script(self, script_name, args=None):
        """Execute a PowerShell script"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
        if args:
            cmd.extend(args)
        
        self.log(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.scripts_dir)
        )
        
        # Log output
        if result.stdout:
            self.log(result.stdout, "OUTPUT")
        if result.stderr:
            self.log(result.stderr, "ERROR")
        
        if result.returncode != 0:
            raise Exception(f"Script failed with return code {result.returncode}")
        
        return result
    
    def step_0_filter(self):
        """Step 0: Filter products by store"""
        self.print_banner("STEP 0: Filter Products by Store")
        
        step_config = self.config['steps']['filter']
        
        if not step_config['enabled']:
            self.log("Step 0 disabled in configuration, skipping...")
            # Return the input file path if filter is disabled
            input_path = self.project_dir / step_config['input']
            if input_path.exists():
                return str(input_path)
            else:
                raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self.log(f"Store ID: {self.config['store_id']}")
        self.log(f"Store Name: {self.config['store_name']}")
        
        # Check if output already exists
        output_file = self.scripts_dir / step_config['output']
        if output_file.exists():
            response = input(f"\nFiltered file already exists: {output_file}\nOverwrite? (y/n): ")
            if response.lower() != 'y':
                self.log("Using existing filtered file")
                return str(output_file)
        
        # Get input file path
        input_file = str(self.project_dir / step_config['input'])
        
        # Run filter script
        self.run_python_script(
            step_config['script'],
            [input_file, str(output_file), str(self.config['store_id'])]
        )
        
        if output_file.exists():
            self.log(f"Filter completed: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"Filter failed: {output_file} not created")
    
    def step_1_export(self):
        """Step 1: Export data from uStore database (DEPRECATED - use filter instead)"""
        self.print_banner("STEP 1: Export from uStore Database")
        
        step_config = self.config['steps'].get('export', {})
        
        if not step_config or not step_config.get('enabled', False):
            self.log("Step 1 (export) not configured or disabled, skipping...")
            return None
        
        self.log("WARNING: PowerShell export step is deprecated")
        self.log("Use store_filter (Step 0) with complete CSV export instead")
        
        # Check if output already exists
        output_file = self.scripts_dir / step_config['output']
        if output_file.exists():
            response = input(f"\nOutput file already exists: {output_file}\nOverwrite? (y/n): ")
            if response.lower() != 'y':
                self.log("Using existing export file")
                return str(output_file)
        
        # Run PowerShell export script
        self.run_powershell_script(step_config['script'])
        
        if output_file.exists():
            self.log(f"Export completed: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"Export failed: {output_file} not created")
    
    def step_2_seo_generation(self, input_file):
        """Step 2: Generate SEO titles and keywords"""
        self.print_banner("STEP 2: Generate SEO Data")
        
        step_config = self.config['steps']['seo_generation']
        
        if not step_config['enabled']:
            self.log("Step 2 disabled in configuration, skipping...")
            return input_file
        
        output_file = self.scripts_dir / step_config['output']
        
        self.run_python_script(
            step_config['script'],
            [input_file, str(output_file)]
        )
        
        if output_file.exists():
            self.log(f"SEO generation completed: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"SEO generation failed: {output_file} not created")
    
    def step_3_asset_linking(self, input_file):
        """Step 3: Link assets (PDFs and images) to products"""
        self.print_banner("STEP 3: Link Assets to Products")
        
        step_config = self.config['steps']['asset_linking']
        
        if not step_config['enabled']:
            self.log("Step 3 disabled in configuration, skipping...")
            return input_file
        
        output_file = self.scripts_dir / step_config['output']
        
        # Get asset paths from config
        assets_dir = str(self.project_dir / self.config['paths']['assets_dir'])
        thumbnails_dir = str(self.project_dir / self.config['paths']['thumbnails_dir'])
        
        self.log(f"Assets directory: {assets_dir}")
        self.log(f"Thumbnails directory: {thumbnails_dir}")
        
        self.run_python_script(
            step_config['script'],
            [input_file, str(output_file), assets_dir, thumbnails_dir]
        )
        
        if output_file.exists():
            self.log(f"Asset linking completed: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"Asset linking failed: {output_file} not created")
    
    def step_4_mdsf_mapping(self, input_file):
        """Step 4: Map fields to MDSF format"""
        self.print_banner("STEP 4: Map to MDSF Format")
        
        step_config = self.config['steps']['mdsf_mapping']
        
        if not step_config['enabled']:
            self.log("Step 4 disabled in configuration, skipping...")
            return input_file
        
        output_file = self.scripts_dir / step_config['output']
        
        self.log(f"Use AutoThumbnail: {self.config['use_auto_thumbnail']}")
        self.log(f"Test Mode: {self.config['test_mode']}")
        if self.config['test_mode']:
            self.log(f"Test Product Limit: {self.config['test_product_limit']}")
        
        self.run_python_script(
            step_config['script'],
            [
                input_file,
                str(output_file),
                str(self.config['use_auto_thumbnail']).lower(),
                str(self.config['test_mode']).lower(),
                str(self.config['test_product_limit'])
            ]
        )
        
        if output_file.exists():
            self.log(f"MDSF mapping completed: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"MDSF mapping failed: {output_file} not created")
    
    def step_5_packaging(self, input_file):
        """Step 5: Create final ZIP package for MDSF import"""
        self.print_banner("STEP 5: Create Import Package")
        
        step_config = self.config['steps']['packaging']
        
        if not step_config['enabled']:
            self.log("Step 5 disabled in configuration, skipping...")
            return None
        
        output_file = self.scripts_dir / step_config['output']
        
        # Get asset paths from config
        assets_dir = str(self.project_dir / self.config['paths']['assets_dir'])
        thumbnails_dir = str(self.project_dir / self.config['paths']['thumbnails_dir'])
        
        self.run_python_script(
            step_config['script'],
            [
                input_file,
                assets_dir,
                thumbnails_dir,
                str(self.config['test_mode']).lower()
            ]
        )
        
        if output_file.exists():
            self.log(f"Package created: {output_file}")
            return str(output_file)
        else:
            raise FileNotFoundError(f"Packaging failed: {output_file} not created")
    
    def run(self, start_from_step=0):
        """Execute the complete migration pipeline"""
        self.state['start_time'] = datetime.now()
        
        self.print_banner("uStore to MDSF Migration Pipeline")
        
        self.log(f"Configuration:")
        self.log(f"  Store: {self.config['store_name']} (ID: {self.config['store_id']})")
        self.log(f"  Test Mode: {self.config['test_mode']}")
        self.log(f"  Auto Thumbnail: {self.config['use_auto_thumbnail']}")
        self.log(f"  Project Directory: {self.project_dir}")
        self.log(f"  Log File: {self.log_file}")
        
        try:
            current_file = None
            
            # Step 0: Filter by Store
            if start_from_step <= 0:
                self.state['current_step'] = 0
                current_file = self.step_0_filter()
                self.state['completed_steps'].append(0)
            
            # Step 1: SEO Generation (formerly step 2)
            if start_from_step <= 1:
                self.state['current_step'] = 1
                if current_file is None:
                    # Fallback to filter output if no file from previous step
                    if 'filter' in self.config['steps']:
                        current_file = str(self.scripts_dir / self.config['steps']['filter']['output'])
                    else:
                        raise FileNotFoundError("No input file for SEO generation. Run filter step first.")
                current_file = self.step_2_seo_generation(current_file)
                self.state['completed_steps'].append(1)
            
            # Step 2: Asset Linking (formerly step 3)
            if start_from_step <= 2:
                self.state['current_step'] = 2
                if current_file is None:
                    current_file = str(self.scripts_dir / self.config['steps']['seo_generation']['output'])
                current_file = self.step_3_asset_linking(current_file)
                self.state['completed_steps'].append(2)
            
            # Step 3: MDSF Mapping (formerly step 4)
            if start_from_step <= 3:
                self.state['current_step'] = 3
                if current_file is None:
                    current_file = str(self.scripts_dir / self.config['steps']['asset_linking']['output'])
                current_file = self.step_4_mdsf_mapping(current_file)
                self.state['completed_steps'].append(3)
            
            # Step 4: Packaging (formerly step 5)
            if start_from_step <= 4:
                self.state['current_step'] = 4
                if current_file is None:
                    current_file = str(self.scripts_dir / self.config['steps']['mdsf_mapping']['output'])
                final_package = self.step_5_packaging(current_file)
                self.state['completed_steps'].append(4)
            
            # Success!
            self.state['end_time'] = datetime.now()
            duration = self.state['end_time'] - self.state['start_time']
            
            self.print_banner("MIGRATION COMPLETE!")
            
            self.log(f"Total duration: {duration}")
            self.log(f"Completed steps: {self.state['completed_steps']}")
            self.log(f"Final package: {final_package}")
            self.log(f"Log file: {self.log_file}")
            
            print("\nNext Steps:")
            print("1. Review the final package")
            print("2. Go to MDSF: Administration > Export / Import")
            print("3. Upload the ZIP file")
            print("4. Verify import results")
            
            return final_package
            
        except Exception as e:
            self.state['end_time'] = datetime.now()
            self.state['failed_steps'].append(self.state['current_step'])
            
            self.print_banner("MIGRATION FAILED!")
            
            self.log(f"Error at step {self.state['current_step']}: {str(e)}", "ERROR")
            self.log(f"Completed steps: {self.state['completed_steps']}")
            self.log(f"Failed at step: {self.state['current_step']}")
            
            print(f"\nTo resume from this step, run:")
            print(f"  python main.py --start-from {self.state['current_step']}")
            
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='uStore to MDSF Migration Pipeline')
    parser.add_argument('--config', default='pipeline_config.json', 
                       help='Path to configuration file')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from specific step (0-4)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (process limited products)')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MigrationPipeline(args.config)
    
    # Override test mode if specified
    if args.test:
        pipeline.config['test_mode'] = True
        print("Test mode enabled via command line")
    
    # Run the pipeline
    try:
        pipeline.run(start_from_step=args.start_from)
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        print(f"Log file: {pipeline.log_file}")
        sys.exit(1)
    except Exception as e:
        print(f"\nPipeline failed: {str(e)}")
        print(f"Log file: {pipeline.log_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()