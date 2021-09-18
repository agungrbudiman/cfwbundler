from urllib import request
from pathlib import Path
import json, re, shutil

shutil.rmtree('cfwbundler-package', ignore_errors=True)

for modulefile in Path('modules').iterdir():
    module = json.loads(modulefile.read_text())
    if module['active'] == True:
        print('[' + module['name'] + ']')
        if not module['version'] == 'latest':
            url = 'https://api.github.com/repos/' + module['repos'] + '/releases/tags/' + module['version']
        else:
            url = 'https://api.github.com/repos/' + module['repos'] + '/releases/latest'
        release = json.load(request.urlopen(url))
    
        modulepath = Path('.tmp', module['name'], release['tag_name'].replace('/',''))
        modulepath.mkdir(parents=True, exist_ok=True)

        cachepath = Path('.cache', module['name'], release['tag_name'].replace('/',''))
        cachepath.mkdir(parents=True, exist_ok=True)

        regex = re.compile( '|'.join(module['assets']) )
        for remote in release['assets']:
            if re.match(regex, remote['name']):
                # download to cache
                assetpath = Path(cachepath, remote['name'])
                if not assetpath.exists():
                    print(remote['name'] + ' -> download')
                    request.urlretrieve(remote['browser_download_url'], assetpath)
                else:
                    print(remote['name'] + ' -> cached')
                # copy to tmp
                shutil.copy(assetpath, modulepath)

        for action in module['actions']:
            # iterate files
            files = modulepath.rglob(action['source'])
            file = next(files, None)
            
            if not file == None:
                print(file.relative_to(modulepath), end='')
                if 'destination' in action:
                    destpath = Path(modulepath, action['destination'])
                    destpath.parent.mkdir(parents=True, exist_ok=True)

                if action['action'] == 'extract':
                    print(' -> extract')
                    shutil.unpack_archive(file, modulepath)
                    file.unlink()

                elif action['action'] == 'copy':
                    print(' -> copy to ' + str(destpath.relative_to(modulepath)))
                    if file.is_dir():
                        shutil.copytree(file, destpath, dirs_exist_ok=True)
                    else:
                        shutil.copy(file, destpath)

                elif action['action'] == 'move':
                    print(' -> move to ' + str(destpath.relative_to(modulepath)))
                    shutil.move(file, destpath)

                elif action['action'] == 'remove':
                    print(' -> remove')
                    if file.is_dir():
                        shutil.rmtree(file)
                    else:
                        file.unlink()

                elif action['action'] == 'replace':
                    print(' -> replace')
                    new = file.read_text().replace(action['old'], action['new'])
                    file.write_text(new)           
            else:
                print(action['source'] + ' -> not found')

        shutil.copytree(modulepath, 'cfwbundler-package', dirs_exist_ok=True)
shutil.make_archive('cfwbundler-package', 'zip', '.', 'cfwbundler-package')
shutil.rmtree('.tmp', ignore_errors=True)
