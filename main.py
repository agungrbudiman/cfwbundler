from urllib import request
from pathlib import Path
import json, re, shutil

shutil.rmtree('cfwbundler-package', ignore_errors=True)
# shutil.rmtree('tmp', ignore_errors=True)

for modulefile in Path('modules').iterdir():
    module = json.loads(modulefile.read_text())
    if module['active'] == True:
        print('[' + module['name'] + ']')
        if not module['version'] == 'latest':
            url = 'https://api.github.com/repos/' + module['repos'] + '/releases'
            releases = json.load(request.urlopen(url))
            for release in releases:
                if release['tag_name'] == module['version']:
                    break
        else:
            url = 'https://api.github.com/repos/' + module['repos'] + '/releases/latest'
            release = json.load(request.urlopen(url))
        
        modulepath = Path('tmp', module['name'], release['tag_name'].replace('/',''))
        modulepath.mkdir(parents=True, exist_ok=True)
        
        for localasset in module['assets']:
            if 'destination' in localasset:
                assetpath = Path(modulepath, localasset['destination'])
                assetpath.parent.mkdir(parents=True, exist_ok=True) #parent directory

            if localasset['action'] == 'download':
                for remoteasset in release['assets']:
                    if re.match(localasset['name'], remoteasset['name']):
                        if not 'destination' in localasset:
                            assetpath = Path(modulepath, remoteasset['name'])
                        print(assetpath, end='')
                        if not assetpath.exists():
                            print(' -> download')
                            request.urlretrieve(remoteasset['browser_download_url'], assetpath)
                        else:
                            print(' -> cached')
                        break
            else:
                moduledir = modulepath.rglob('*')
                for file in moduledir:
                    if re.match(localasset['name'], file.name):
                        print(file, end='')
                        if localasset['action'] == 'extract':
                            print(' -> extract')
                            shutil.unpack_archive(file, modulepath)

                        elif localasset['action'] == 'copy':
                            print(' -> copy')
                            if file.is_dir():
                                shutil.copytree(file, assetpath, dirs_exist_ok=True)
                            else:
                                shutil.copy(file, assetpath)

                        elif localasset['action'] == 'move':
                            print(' -> move')
                            shutil.move(file, assetpath)

                        elif localasset['action'] == 'remove':
                            print(' -> remove')
                            if file.is_dir():
                                shutil.rmtree(file)
                            else:
                                file.unlink()
                        break

        shutil.copytree(modulepath, 'cfwbundler-package', dirs_exist_ok=True, ignore=shutil.ignore_patterns('*.zip'))
shutil.make_archive('cfwbundler-package', 'zip', '.', 'cfwbundler-package')
