import os
import json
import configparser

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default if it doesn't exist"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration"""
        self.config['DATABASE'] = {
            'Type': 'sqlite',
            'Path': 'photo_manager.db',
            'Host': 'localhost',
            'Port': '3306',
            'Name': 'photo_manager',
            'User': 'user',
            'Password': 'password'
        }
        
        # Save the default config
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_database_url(self):
        """Generate database URL based on configuration"""
        db_type = self.config.get('DATABASE', 'Type', fallback='sqlite')
        
        if db_type.lower() == 'sqlite':
            db_path = self.config.get('DATABASE', 'Path', fallback='photo_manager.db')
            return f'sqlite:///{db_path}'
        
        elif db_type.lower() == 'mysql':
            host = self.config.get('DATABASE', 'Host', fallback='localhost')
            port = self.config.get('DATABASE', 'Port', fallback='3306')
            name = self.config.get('DATABASE', 'Name', fallback='photo_manager')
            user = self.config.get('DATABASE', 'User', fallback='user')
            password = self.config.get('DATABASE', 'Password', fallback='password')
            return f'mysql+pymysql://{user}:{password}@{host}:{port}/{name}'
        
        elif db_type.lower() == 'postgresql':
            host = self.config.get('DATABASE', 'Host', fallback='localhost')
            port = self.config.get('DATABASE', 'Port', fallback='5432')
            name = self.config.get('DATABASE', 'Name', fallback='photo_manager')
            user = self.config.get('DATABASE', 'User', fallback='user')
            password = self.config.get('DATABASE', 'Password', fallback='password')
            return f'postgresql://{user}:{password}@{host}:{port}/{name}'
        
        else:
            # Default to SQLite if type is not recognized
            return 'sqlite:///photo_manager.db'