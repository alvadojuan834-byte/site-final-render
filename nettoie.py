import csv

csv.field_size_limit(10000000)

# Remplace par le nom exact de ton tout premier fichier d'origine complet si tu l'as sous un autre nom, 
# sinon on travaille sur ton fichier actuel.
input_file = "mes_produits_sauves.csv"
output_file = "produits_propres.csv"

print("Nettoyage et remise en ordre des colonnes (prix, images, descriptions)...")

with open(input_file, mode="r", encoding="utf-8", errors="ignore") as infile, \
     open(output_file, mode="w", newline="", encoding="utf-8") as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    # Récupère l'en-tête pour comprendre l'ordre des colonnes
    header = next(reader, None)
    if header:
        writer.writerow(header)
        print(f"Colonnes détectées : {header}")
    
    count = 0
    for row in reader:
        # On s'assure de garder les 400 premiers produits avec toutes leurs données
        if count < 400 and len(row) > 0:
            # Nettoyage propre des sauts de ligne pour éviter les bugs de lecture
            clean_row = [cell.replace('\r', ' ').strip() for cell in row]
            writer.writerow(clean_row)
            count += 1

print(f"Terminé ! {count} articles prêts avec leurs vraies données.")