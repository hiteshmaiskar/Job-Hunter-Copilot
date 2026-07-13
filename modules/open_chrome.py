'''
product: Job-Hunter-Copilot
version: v1.2026-07
'''

from modules.helpers import get_default_temp_profile, make_directories
from config.settings import run_in_background, stealth_mode, disable_extensions, safe_mode, file_name, failed_file_name, logs_folder_path, generated_resume_path
from config.questions import default_resume_path
if stealth_mode:
    import undetected_chromedriver as uc
else: 
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import find_default_profile_directory, critical_error_log, print_lg
from selenium.common.exceptions import SessionNotCreatedException
import subprocess, re, shutil, os

# Directory to cache downloaded ChromeDrivers (project root /drivers/)
_DRIVER_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'drivers')

def get_chrome_major_version() -> int | None:
    '''
    Detects the installed Google Chrome major version from the Windows registry.
    Returns the major version as an int, or None if it cannot be determined.
    '''
    try:
        reg_paths = [
            r'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon',
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon',
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon',
        ]
        for path in reg_paths:
            try:
                output = subprocess.check_output(
                    f'reg query "{path}" /v version',
                    shell=True, stderr=subprocess.DEVNULL
                ).decode()
                match = re.search(r'version\s+REG_SZ\s+([\d.]+)', output)
                if match:
                    major = int(match.group(1).split('.')[0])
                    print_lg(f"Detected Chrome version: {match.group(1)} (major: {major})")
                    return major
            except Exception:
                continue
    except Exception as e:
        print_lg(f"Could not detect Chrome version from registry: {e}")
    return None

def _get_cached_driver_path(chrome_version: int) -> str | None:
    '''Returns the path to the cached ChromeDriver if it exists for the given version.'''
    if chrome_version:
        path = os.path.join(_DRIVER_CACHE_DIR, f'chromedriver_{chrome_version}.exe')
        if os.path.isfile(path):
            return path
    return None

def _cache_driver(driver, chrome_version: int) -> None:
    '''Copies the freshly downloaded/patched ChromeDriver to the local cache directory.'''
    try:
        src = driver.service.path
        if not src or not os.path.isfile(src):
            return
        os.makedirs(_DRIVER_CACHE_DIR, exist_ok=True)
        dst = os.path.join(_DRIVER_CACHE_DIR, f'chromedriver_{chrome_version}.exe')
        if not os.path.isfile(dst):
            shutil.copy2(src, dst)
            print_lg(f"ChromeDriver cached → {dst} (will be reused on future runs)")
    except Exception as e:
        print_lg(f"Could not cache ChromeDriver (non-fatal): {e}")

def _create_stealth_driver(options):
    '''
    Creates an undetected Chrome driver, using a locally cached ChromeDriver
    binary when available to avoid re-downloading on every run.
    '''
    chrome_version = get_chrome_major_version()
    cached_path    = _get_cached_driver_path(chrome_version) if chrome_version else None

    if cached_path:
        print_lg(f"Using cached ChromeDriver ({chrome_version}) → {cached_path}")
        driver = uc.Chrome(driver_executable_path=cached_path, options=options, version_main=chrome_version)
    else:
        print_lg(f"ChromeDriver not cached — downloading for Chrome {chrome_version} (one-time, will be cached)...")
        driver = uc.Chrome(options=options, version_main=chrome_version) if chrome_version else uc.Chrome(options=options)
        if chrome_version:
            _cache_driver(driver, chrome_version)
    return driver

def createChromeSession(isRetry: bool = False):
    make_directories([file_name,failed_file_name,logs_folder_path+"/screenshots",default_resume_path,generated_resume_path+"/temp"])
    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:   options.add_argument("--headless")
    if disable_extensions:  options.add_argument("--disable-extensions")

    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")
    profile_dir = find_default_profile_directory()
    if isRetry:
        print_lg("Will login with a guest profile, browsing history will not be saved in the browser!")
    elif profile_dir and not safe_mode:
        options.add_argument(f"--user-data-dir={profile_dir}")
    else:
        print_lg("Logging in with a guest profile, Web history will not be saved!")
        options.add_argument(f"--user-data-dir={get_default_temp_profile()}")
    if stealth_mode:
        driver = _create_stealth_driver(options)
    else: driver = webdriver.Chrome(options=options) #, service=Service(executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe"))
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
    return options, driver, actions, wait

try:
    options, driver, actions, wait = None, None, None, None
    options, driver, actions, wait = createChromeSession()
except SessionNotCreatedException as e:
    critical_error_log("Failed to create Chrome Session, retrying with guest profile", e)
    options, driver, actions, wait = createChromeSession(True)
except Exception as e:
    msg = 'Seems like Google Chrome is out dated. Update browser and try again! \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e,TimeoutError): msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    from pyautogui import alert
    alert(msg, "Error in opening chrome")
    try: driver.quit()
    except NameError: exit()
    
