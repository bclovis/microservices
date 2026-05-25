import pandas as pd
import  numpy as np

try : 
    df = pd.read_excel('vgsales.xlsx')
    print('File loaded successfully.')

    print('First 5 rows of the dataset:')
    print(df.head())

    print('Summary statistics of the dataset:')
    print(df.info())
    
    # 1. EXPLORATION DES DONNÉES
    print('\n' + '='*50)
    print('1. EXPLORATION DES DONNÉES')
    print('='*50)
    
    # Forme du dataset
    print(f'\nForme du dataset: {df.shape}')
    print(f'Nombre de lignes: {df.shape[0]}')
    print(f'Nombre de colonnes: {df.shape[1]}')
    
    # Colonnes disponibles
    print(f'\nColonnes disponibles:')
    for i, col in enumerate(df.columns, 1):
        print(f'{i}. {col}')
    
    # Valeurs manquantes
    print(f'\nValeurs manquantes par colonne:')
    missing_values = df.isnull().sum()
    for col, missing in missing_values.items():
        if missing > 0:
            percentage = (missing / len(df)) * 100
            print(f'{col}: {missing} ({percentage:.2f}%)')
        else:
            print(f'{col}: {missing}')
    
    # Statistiques descriptives pour les colonnes numériques
    print(f'\nStatistiques descriptives (colonnes numériques):')
    print(df.describe())
    
    # 2. ANALYSE DES GENRES
    print('\n' + '='*50)
    print('2. ANALYSE DES GENRES')
    print('='*50)
    
    # Nombre de jeux par genre
    print(f'\nNombre de jeux par genre:')
    genre_count = df['Genre'].value_counts()
    print(genre_count)
    
    # Ventes totales par genre
    print(f'\nVentes totales par genre (en millions):')
    genre_sales = df.groupby('Genre')['Global_Sales'].sum().sort_values(ascending=False)
    print(genre_sales)
    
    # Ventes moyennes par genre
    print(f'\nVentes moyennes par genre (en millions):')
    genre_avg_sales = df.groupby('Genre')['Global_Sales'].mean().sort_values(ascending=False)
    print(genre_avg_sales)
    
    # Genre le plus populaire
    print(f'\nGenre avec le plus de jeux: {genre_count.index[0]} ({genre_count.iloc[0]} jeux)')
    print(f'Genre avec les meilleures ventes totales: {genre_sales.index[0]} ({genre_sales.iloc[0]:.2f} millions)')
    print(f'Genre avec les meilleures ventes moyennes: {genre_avg_sales.index[0]} ({genre_avg_sales.iloc[0]:.2f} millions par jeu)')
    
    # 3. ANALYSE TEMPORELLE
    print('\n' + '='*50)
    print('3. ANALYSE TEMPORELLE')
    print('='*50)
    
    # Nettoyage des données - supprimer les années manquantes
    df_clean_year = df.dropna(subset=['Year'])
    
    # Évolution du nombre de jeux sortis par année
    print(f'\nNombre de jeux sortis par année (dernières 10 années):')
    games_per_year = df_clean_year['Year'].value_counts().sort_index()
    print(games_per_year.tail(10))
    
    # Évolution des ventes totales par année
    print(f'\nVentes totales par année (dernières 10 années, en millions):')
    sales_per_year = df_clean_year.groupby('Year')['Global_Sales'].sum().sort_index()
    print(sales_per_year.tail(10))
    
    # Ventes moyennes par jeu par année
    print(f'\nVentes moyennes par jeu par année (dernières 10 années, en millions):')
    avg_sales_per_year = df_clean_year.groupby('Year')['Global_Sales'].mean().sort_index()
    print(avg_sales_per_year.tail(10))
    
    # Années avec le plus de jeux et les meilleures ventes
    best_year_count = games_per_year.idxmax()
    best_year_sales = sales_per_year.idxmax()
    print(f'\nAnnée avec le plus de jeux sortis: {int(best_year_count)} ({games_per_year.max()} jeux)')
    print(f'Année avec les meilleures ventes totales: {int(best_year_sales)} ({sales_per_year.max():.2f} millions)')
    
    # 4. ANALYSE PAR PLATEFORME
    print('\n' + '='*50)
    print('4. ANALYSE PAR PLATEFORME')
    print('='*50)
    
    # Nombre de jeux par plateforme
    print(f'\nTop 10 des plateformes avec le plus de jeux:')
    platform_count = df['Platform'].value_counts()
    print(platform_count.head(10))
    
    # Ventes totales par plateforme
    print(f'\nTop 10 des plateformes par ventes totales (en millions):')
    platform_sales = df.groupby('Platform')['Global_Sales'].sum().sort_values(ascending=False)
    print(platform_sales.head(10))
    
    # Ventes moyennes par jeu par plateforme
    print(f'\nTop 10 des plateformes par ventes moyennes par jeu (en millions):')
    platform_avg_sales = df.groupby('Platform')['Global_Sales'].mean().sort_values(ascending=False)
    print(platform_avg_sales.head(10))
    
    # Analyse des ventes par région pour le top 5 des plateformes
    print(f'\nVentes par région pour le top 5 des plateformes (en millions):')
    top_platforms = platform_sales.head(5).index
    for platform in top_platforms:
        platform_data = df[df['Platform'] == platform]
        na_sales = platform_data['NA_Sales'].sum()
        eu_sales = platform_data['EU_Sales'].sum()
        jp_sales = platform_data['JP_Sales'].sum()
        other_sales = platform_data['Other_Sales'].sum()
        print(f'\n{platform}:')
        print(f'  Amérique du Nord: {na_sales:.2f}')
        print(f'  Europe: {eu_sales:.2f}')
        print(f'  Japon: {jp_sales:.2f}')
        print(f'  Autres: {other_sales:.2f}')
    
    # 5. TOP DES JEUX ET ÉDITEURS
    print('\n' + '='*50)
    print('5. TOP DES JEUX ET ÉDITEURS')
    print('='*50)
    
    # Top 10 des jeux les plus vendus
    print(f'\nTop 10 des jeux les plus vendus (en millions):')
    top_games = df.nlargest(10, 'Global_Sales')[['Name', 'Platform', 'Year', 'Genre', 'Publisher', 'Global_Sales']]
    for i, (_, game) in enumerate(top_games.iterrows(), 1):
        print(f'{i:2}. {game["Name"]} ({game["Platform"]}, {int(game["Year"]) if pd.notna(game["Year"]) else "N/A"}) - {game["Global_Sales"]} millions')
    
    # Top 10 des éditeurs par ventes totales
    print(f'\nTop 10 des éditeurs par ventes totales (en millions):')
    publisher_sales = df.groupby('Publisher')['Global_Sales'].sum().sort_values(ascending=False)
    print(publisher_sales.head(10))
    
    # Nombre de jeux par éditeur (top 10)
    print(f'\nTop 10 des éditeurs par nombre de jeux:')
    publisher_count = df['Publisher'].value_counts()
    print(publisher_count.head(10))
    
    # Top 5 des jeux par région
    print(f'\nTop 5 des jeux les plus vendus par région:')
    
    regions = [('NA_Sales', 'Amérique du Nord'), ('EU_Sales', 'Europe'), 
               ('JP_Sales', 'Japon'), ('Other_Sales', 'Autres régions')]
    
    for sales_col, region_name in regions:
        print(f'\n{region_name}:')
        top_region = df.nlargest(5, sales_col)[['Name', 'Platform', sales_col]]
        for i, (_, game) in enumerate(top_region.iterrows(), 1):
            print(f'  {i}. {game["Name"]} ({game["Platform"]}) - {game[sales_col]} millions')
    
    # Statistiques générales intéressantes
    print(f'\n' + '='*50)
    print('STATISTIQUES GÉNÉRALES')
    print('='*50)
    
    total_global_sales = df['Global_Sales'].sum()
    avg_game_sales = df['Global_Sales'].mean()
    median_game_sales = df['Global_Sales'].median()
    
    print(f'Ventes totales de tous les jeux: {total_global_sales:.2f} millions')
    print(f'Ventes moyennes par jeu: {avg_game_sales:.2f} millions')
    print(f'Ventes médianes par jeu: {median_game_sales:.2f} millions')
    print(f'Nombre total de jeux: {len(df)}')
    print(f'Nombre d\'éditeurs uniques: {df["Publisher"].nunique()}')
    print(f'Nombre de plateformes uniques: {df["Platform"].nunique()}')
    print(f'Nombre de genres uniques: {df["Genre"].nunique()}')
    
    # Répartition des ventes par région
    na_total = df['NA_Sales'].sum()
    eu_total = df['EU_Sales'].sum() 
    jp_total = df['JP_Sales'].sum()
    other_total = df['Other_Sales'].sum()
    
    print(f'\nRépartition des ventes mondiales par région:')
    print(f'Amérique du Nord: {na_total:.2f} millions ({na_total/total_global_sales*100:.1f}%)')
    print(f'Europe: {eu_total:.2f} millions ({eu_total/total_global_sales*100:.1f}%)')
    print(f'Japon: {jp_total:.2f} millions ({jp_total/total_global_sales*100:.1f}%)')
    print(f'Autres régions: {other_total:.2f} millions ({other_total/total_global_sales*100:.1f}%)')
    
except FileNotFoundError:
    print("The file 'vgsales.xlsx' was not found. Please ensure it is in the correct directory.")
    