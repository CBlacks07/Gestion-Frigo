# 📦 Instructions pour créer l'installeur Gestion-Frigo

Ce guide vous explique comment créer un installeur Windows (.exe) pour distribuer l'application Gestion-Frigo.

## 🛠️ Prérequis

1. **Python 3.8+** installé
2. **PyInstaller** (sera installé automatiquement)
3. **Inno Setup** (optionnel, pour créer un installeur professionnel)
   - Télécharger depuis : https://jrsoftware.org/isdl.php

## 📋 Méthode 1 : Créer uniquement l'exécutable (.exe)

### Étape 1 : Exécuter le script de build

Double-cliquez sur `build.bat` ou exécutez dans PowerShell :

```powershell
.\build.bat
```

### Étape 2 : Résultat

L'exécutable se trouvera dans : `dist\Gestion-Frigo.exe`

Vous pouvez copier ce fichier et le distribuer. Il est **standalone** (pas besoin d'installer Python).

## 📦 Méthode 2 : Créer un installeur Windows complet (recommandé)

### Étape 1 : Créer l'exécutable

```powershell
.\build.bat
```

### Étape 2 : Installer Inno Setup

1. Télécharger Inno Setup : https://jrsoftware.org/isdl.php
2. Installer avec les options par défaut

### Étape 3 : Compiler l'installeur

1. Ouvrir **Inno Setup Compiler**
2. Menu **File > Open** → Sélectionner `installer.iss`
3. Menu **Build > Compile** (ou appuyer sur F9)

### Étape 4 : Résultat

L'installeur se trouvera dans : `installer_output\Gestion-Frigo-Setup.exe`

Cet installeur :
- ✅ Installe l'application dans `Program Files`
- ✅ Crée un raccourci dans le menu Démarrer
- ✅ Propose de créer un raccourci sur le Bureau
- ✅ Inclut un désinstalleur

## 🚀 Distribution

Pour distribuer l'application :

**Option Simple** : Donnez le fichier `dist\Gestion-Frigo.exe`
- Les utilisateurs le copient où ils veulent et double-cliquent

**Option Professionnelle** : Donnez le fichier `Gestion-Frigo-Setup.exe`
- Les utilisateurs exécutent l'installeur
- Installation automatique avec désinstalleur

## 📝 Notes importantes

### Taille du fichier
L'exécutable fera environ **80-150 MB** car il inclut :
- Python
- PyQt6
- ReportLab
- Toutes les bibliothèques nécessaires

### Antivirus
Certains antivirus peuvent signaler l'exécutable comme suspect (faux positif).
Solution : Signer le code avec un certificat de signature de code (payant).

### Personnalisation

#### Ajouter une icône
1. Créez ou téléchargez un fichier `.ico` (icône Windows)
2. Nommez-le `icon.ico` et placez-le dans le dossier racine
3. Dans `build_installer.spec`, ligne 53, remplacez :
   ```python
   icon=None,
   ```
   par :
   ```python
   icon='icon.ico',
   ```

#### Modifier les informations
Éditez `installer.iss` pour changer :
- Nom de l'entreprise
- Version
- Textes de l'installeur

## 🐛 Résolution de problèmes

### Erreur "PyInstaller not found"
```powershell
pip install pyinstaller
```

### L'exécutable ne se lance pas
Testez d'abord avec :
```powershell
pyinstaller --onefile --windowed --name Gestion-Frigo main.py
```

### Erreur "Module not found"
Ajoutez le module manquant dans `build_installer.spec` section `hiddenimports`.

## 📞 Support

Si vous rencontrez des problèmes, vérifiez :
1. Que l'application fonctionne avec `python main.py`
2. Que toutes les dépendances sont installées (`pip install -r requirements.txt`)
3. Les messages d'erreur détaillés
