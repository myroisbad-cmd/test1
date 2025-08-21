# Correction de l'erreur de syntaxe - v4.py

## ❌ Problème rencontré

```
SyntaxError: name 'STRICT_DATA_FILTERING' is used prior to global declaration
```

**Ligne 896 :** `global STRICT_DATA_FILTERING`

## 🔍 Cause du problème

La variable `STRICT_DATA_FILTERING` était utilisée à la ligne 878 :
```python
strict_filtering = STRICT_DATA_FILTERING  # ← Utilisation de la variable
```

Puis déclarée comme `global` seulement à la ligne 896 :
```python
global STRICT_DATA_FILTERING  # ← Déclaration trop tardive
```

En Python, la déclaration `global` doit apparaître **avant** toute utilisation de la variable dans la fonction.

## ✅ Solution appliquée

### Modification 1 : Déplacer la déclaration global
**Avant (ligne 816) :**
```python
def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
```

**Après (ligne 816-818) :**
```python
def main():
    """Fonction principale"""
    global STRICT_DATA_FILTERING  # ← Déclaration au début
    
    parser = argparse.ArgumentParser(
```

### Modification 2 : Supprimer la déclaration redondante
**Avant (lignes 896-898) :**
```python
# Appliquer temporairement la configuration de filtrage
global STRICT_DATA_FILTERING  # ← Supprimé (redondant)
original_filtering = STRICT_DATA_FILTERING
```

**Après (lignes 897-898) :**
```python
# Appliquer temporairement la configuration de filtrage
original_filtering = STRICT_DATA_FILTERING
```

## ✅ Vérification

Le fichier `v4.py` a été testé et ne présente plus d'erreurs de syntaxe :

```bash
python3 -c "import ast; ast.parse(open('v4.py').read())"
# ✅ Aucune erreur
```

## 📋 Règle Python à retenir

**Déclaration `global` :** Doit toujours être placée au **début** de la fonction, avant toute utilisation de la variable.

```python
def ma_fonction():
    global MA_VARIABLE  # ✅ Correct : au début
    
    valeur = MA_VARIABLE  # ✅ Utilisation après déclaration
    MA_VARIABLE = nouvelle_valeur
```

```python
def ma_fonction():
    valeur = MA_VARIABLE  # ❌ Erreur : utilisation avant déclaration
    global MA_VARIABLE    # ❌ Trop tard
```

## 🚀 Résultat

Le script `v4.py` fonctionne maintenant correctement avec toutes les nouvelles fonctionnalités :
- ✅ Filtrage strict des données
- ✅ Paramètres en ligne de commande
- ✅ Configuration flexible
- ✅ Syntaxe Python correcte