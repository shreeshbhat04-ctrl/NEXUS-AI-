import os
import re

base_dir = r"c:\Users\shree\project\Cure-Quest\frontend\src"

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Determine file's new relative directory level compared to src
    rel_path = os.path.relpath(file_path, base_dir)
    parts = rel_path.split(os.sep)
    
    modified = False

    # 1. Update imports in App.tsx (which is directly in src)
    if rel_path == "App.tsx":
        replacements = [
            (r"from '\./components/Layout'", "from './patient/components/Layout'"),
            (r"from '\./screens/DashboardScreen'", "from './patient/screens/DashboardScreen'"),
            (r"from '\./screens/CareMazeScreen'", "from './patient/screens/CareMazeScreen'"),
            (r"from '\./screens/MedicationHubScreen'", "from './patient/screens/MedicationHubScreen'"),
            (r"from '\./screens/HistoryScreen'", "from './patient/screens/HistoryScreen'"),
            (r"from '\./screens/HITLScreen'", "from './patient/screens/HITLScreen'"),
            (r"from '\./screens/LoginScreen'", "from './patient/screens/LoginScreen'"),
            (r"from '\./screens/AboutScreen'", "from './patient/screens/AboutScreen'"),
            (r"from '\./screens/Profile'", "from './patient/screens/Profile'"),
            (r"from '\./components/VoiceAssistant'", "from './patient/components/VoiceAssistant'"),
            (r"from '\./hooks/useWorkspace'", "from './patient/hooks/useWorkspace'"),
            (r"from '\./screens/DoctorWorkspaceScreen'", "from './doctor/screens/DoctorWorkspaceScreen'"),
        ]
        new_content = content
        for pat, repl in replacements:
            new_content = re.sub(pat, repl, new_content)
        if new_content != content:
            content = new_content
            modified = True

    # 2. Update imports in files inside patient/screens/
    elif parts[0] == "patient" and parts[1] == "screens":
        # Files are at patient/screens/Name.tsx
        # Old path was screens/Name.tsx, which was 1 level deep. New path is 2 levels deep.
        # Relative imports to lib/ or components/ was `../components/...` or `../lib/...`
        # Now components are in patient/components (use `../components`) or shared/components (use `../../shared/components`)
        # lib is in shared/lib (use `../../shared/lib`)
        
        # Replace '../lib/api' with '../../shared/lib/api'
        # Replace '../lib/ingredients' with '../../shared/lib/ingredients'
        new_content = re.sub(r"from '\.\./lib/api'", "from '../../shared/lib/api'", content)
        new_content = re.sub(r"from '\.\./lib/ingredients'", "from '../../shared/lib/ingredients'", new_content)
        
        # Replace '../components/States' with '../../shared/components/States'
        # Replace '../components/ui' with '../../shared/components/ui'
        # Replace '../components/DoctorCard' with '../../shared/components/DoctorCard'
        new_content = re.sub(r"from '\.\./components/States'", "from '../../shared/components/States'", new_content)
        new_content = re.sub(r"from '\.\./components/ui'", "from '../../shared/components/ui'", new_content)
        new_content = re.sub(r"from '\.\./components/DoctorCard'", "from '../../shared/components/DoctorCard'", new_content)
        
        # Replace '../components/VoiceAssistant' with '../components/VoiceAssistant' (stays 1 dot level: screens to components is ../components)
        # Wait, since patient screens were at screens/Name.tsx and layout/voice assistant was at components/Layout.tsx,
        # old import was `../components/VoiceAssistant`.
        # Now patient screen is patient/screens/Name.tsx and voice assistant is patient/components/VoiceAssistant.tsx.
        # So screens to components is still `../components/VoiceAssistant`. Thus no change needed for ../components/VoiceAssistant!
        # Same for `../hooks/useWorkspace` (screens to hooks is ../hooks/useWorkspace). No change needed.
        if new_content != content:
            content = new_content
            modified = True

    # 3. Update imports in files inside patient/components/
    elif parts[0] == "patient" and parts[1] == "components":
        # Layout.tsx, ChatAssistant.tsx, VoiceAssistant.tsx
        # Old path was components/Layout.tsx. New path is patient/components/Layout.tsx.
        
        # In Layout.tsx:
        # `../assets/logo.png` needs to be `../../assets/logo.png`
        # `../lib/api` needs to be `../../shared/lib/api`
        # `../screens/...` was imported? No, no screens imported in Layout.
        new_content = content
        new_content = re.sub(r"from '\.\./lib/api'", "from '../../shared/lib/api'", new_content)
        new_content = re.sub(r"from '\.\./lib/ingredients'", "from '../../shared/lib/ingredients'", new_content)
        new_content = re.sub(r"from '\.\./components/States'", "from '../../shared/components/States'", new_content)
        new_content = re.sub(r"from '\.\./components/ui'", "from '../../shared/components/ui'", new_content)
        new_content = re.sub(r"import logo from '\.\./assets/logo\.png'", "import logo from '../../assets/logo.png'", new_content)
        
        # ChatAssistant.tsx or VoiceAssistant.tsx might import relative files.
        # ChatAssistant.tsx was in components/ChatAssistant.tsx.
        # It imported:
        # `import { api } from '../lib/api'` -> now `../../shared/lib/api`
        # `import { Pill } from './ui'` (was in same dir) -> now `../../shared/components/ui`
        # `import { ErrorState, LoadingState } from './States'` -> now `../../shared/components/States`
        new_content = re.sub(r"from '\./ui'", "from '../../shared/components/ui'", new_content)
        new_content = re.sub(r"from '\./States'", "from '../../shared/components/States'", new_content)
        
        if new_content != content:
            content = new_content
            modified = True

    # 4. Update imports in patient/hooks/
    elif parts[0] == "patient" and parts[1] == "hooks":
        # useWorkspace.ts:
        # `import { api } from '../lib/api'` -> now `../../shared/lib/api`
        new_content = re.sub(r"from '\.\./lib/api'", "from '../../shared/lib/api'", content)
        if new_content != content:
            content = new_content
            modified = True

    # 5. Update imports in doctor/screens/
    elif parts[0] == "doctor" and parts[1] == "screens":
        # DoctorWorkspaceScreen.tsx
        # Old path: screens/DoctorWorkspaceScreen.tsx
        # Imported:
        # `import { api } from '../lib/api'` -> `../../shared/lib/api`
        # `import { ErrorState, LoadingState } from '../components/States'` -> `../../shared/components/States`
        # `import { Pill, SectionShell } from '../components/ui'` -> `../../shared/components/ui`
        # `import { DoctorCard } from '../components/DoctorCard'` -> `../../shared/components/DoctorCard`
        new_content = re.sub(r"from '\.\./lib/api'", "from '../../shared/lib/api'", content)
        new_content = re.sub(r"from '\.\./components/States'", "from '../../shared/components/States'", new_content)
        new_content = re.sub(r"from '\.\./components/ui'", "from '../../shared/components/ui'", new_content)
        new_content = re.sub(r"from '\.\./components/DoctorCard'", "from '../../shared/components/DoctorCard'", new_content)
        if new_content != content:
            content = new_content
            modified = True

    # 6. Update imports in shared/components/
    elif parts[0] == "shared" and parts[1] == "components":
        # DoctorCard.tsx, ui.tsx, States.tsx
        # If they import `./ui` or similar, they are in the same dir so it is fine.
        # But if they import from `../lib/api`, it is now `../../shared/lib/api` or `../lib/api`.
        # Wait, from shared/components/ to shared/lib/ is `../lib/`.
        # Previously: from components/ to lib/ was `../lib/`.
        # So `../lib/` is STILL `../lib/`! No change needed.
        pass

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed imports in {rel_path}")

# Run recursively
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".ts") or file.endswith(".tsx"):
            process_file(os.path.join(root, file))
