import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn import preprocessing
import time
import math
import random
import copy
import operator

start_time = time.time()

DB_PATH = 'Pokemon.csv'
pokemon_db = pd.read_csv(DB_PATH)   #cargando archivo de Pokemon
pokemon_db.drop_duplicates(subset = "#", keep = 'first', inplace = True)
pokemon_db = pokemon_db.drop(['Generation'], axis = 1) #no toma en cuenta generacion
vector_db = pokemon_db #db en el que se usara OH-Encoding y se modificarán características
vector_db['Type 2'] = vector_db['Type 2'].fillna("None") #reemplazamos NaN en type 2 por None
encoder = OneHotEncoder(handle_unknown='ignore')
vector_db["Legendary"] = vector_db["Legendary"].astype(int)
#vector_db.drop_duplicates(subset = "#", keep = 'first', inplace = True) #se eliminan ids duplicados por mega evoluciones
object_cols = ["Type 1", "Type 2"]

vector_db = pd.get_dummies(data = vector_db, columns = object_cols) #one hot encoder para type 1 y 2

cols_to_norm = ['Total','HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed'] #normalizar para que no influyan tanto los stats
vector_db[cols_to_norm] = vector_db[cols_to_norm].apply(lambda x: (x - x.min()) / (x.max() - x.min()))

poke_list = vector_db.values.tolist()

random.shuffle(poke_list)  #se desordena la lista para que el arbol quede balanceado

class PokeNode:
    poke_id = 0
    poke_name = None
    right = None
    left = None
    parent = None
    poke_data = None
    visited = False
    def __init__(self, id, name, data):
        self.poke_id = id
        self.poke_data = data
        self.poke_name = name

        
class Pokedex:  #en realidad es un kd tree pero le puse pokedex para ser pokeconsistente
    root = None
    dim = 0
    pokemons = []  #aca se almacenan todos los pokemon para buscar sus datos por id
    vectorized_pokemons = []
    def __init__(self, dim):
        self.dim = dim
        
    def insert(self, node):
        i = 0
        current_node = self.root
        if not self.root:
            self.root = node
        
        else:
            while True:
                direction = node.poke_data[i] - current_node.poke_data[i]
                if direction >= 0: #current node es menor, por lo que vamos a la derecha
                    next_node = current_node.right
                    if not next_node: #si el nodo esta vacio
                        current_node.right = node
                        node.parent = current_node
                        break
                    current_node = current_node.right
                else:
                    next_node = current_node.left
                    if not next_node: #si el nodo esta vacio
                        current_node.left = node
                        node.parent = current_node
                        break
                    current_node = current_node.left                    
 
                i = (i+1) % self.dim  # i+1 mod dim
                
    def fake_insert(self, node, k):  #llega hasta el final pero no inserta el nodo, sino que retorna el nodo parent
        i = 0
        knp = []
        max_size = k
        current_node = self.root
        current_node.visited = True;

        while True:
            if len(knp) < max_size:
                knp.append([self.manhattan_distance(current_node,node), current_node])

            else:

                dist = self.manhattan_distance(current_node, node)
                if knp[0][0] > dist: #si el current es mejor que el peor de la lista
                    knp[0] = [dist, current_node]

                
            direction = node.poke_data[i] - current_node.poke_data[i]
            if direction >= 0: #current node es menor, por lo que vamos a la derecha
                next_node = current_node.right
                if not next_node: #si el nodo esta vacio
                    knp = sorted(knp,key = operator.itemgetter(0),reverse = True)
                    return knp
                current_node = current_node.right
                current_node.visited = True
            else:
                next_node = current_node.left
                if not next_node: #si el nodo esta vacio
                    knp = sorted(knp, key = operator.itemgetter(0), reverse = True)
                    return knp
                current_node = current_node.left
                current_node.visited = True                    
            i = (i+1) % self.dim  # i+1 mod dim  


      
        
    def search_knp(self, node, k): #k nearest pokemon
        pokelist = []
        max_size = k
        current_node = self.root
        pokelist = self.fake_insert(node, k) #primero llegamos al final del arbol ubicando el pokemon

        for pokemon in pokelist:
            pokelist = self.search_subtree(pokemon[1], pokelist, k, node)
        return pokelist

    
    
    def manhattan_distance(self, node1, node2): #en realidad no es manhattan distance porque usa dos tipos de dist
        dist = 0
        for i in range(7): #para atributos no categoricos normalizados
            dist += abs(float(node1.poke_data[i]) - float(node2.poke_data[i])) 
        while i < 45:     #compara atributos categoricos por un criterio de tipo Jacard
            if node1.poke_data[i] == node2.poke_data[i]:
                dist-= 0.7 #factor arbitrario por ser del mismo tipo o legendarios
            i+=1
        
        
        return dist
                    
    def search_subtree(self, node, pokelist, k, search_node):
        new_pokelist = pokelist
        nodes_to_check = []
        nodes_to_check.append(node)
        new_nodes = []
        while nodes_to_check:
            new_nodes = []
            for pokemon in nodes_to_check:
                if pokemon.left and not pokemon.left.visited: #si hay nodo a la izquierda no visitado
                    if len(new_pokelist) < k:
                        new_pokelist.append([self.manhattan_distance(pokemon.left,search_node), pokemon])
                        new_nodes.append(pokemon.left)
                    else:
                        dist = self.manhattan_distance(pokemon.left, search_node)
                        new_pokelist = sorted(new_pokelist, key = operator.itemgetter(0), reverse = True)
                        if new_pokelist[0][0] > dist:
                            new_pokelist[0] = [dist, pokemon.left]
                            new_nodes.append(pokemon.left)
                  #      else:                                  #si se descomenta esto busca todo el arbol 
                    #        new_nodes.append(pokemon.left)

                if pokemon.right and not pokemon.right.visited: #si hay nodo a la derecha no visitado
                    if len(new_pokelist) < k:
                        new_pokelist.append([self.manhattan_distance(pokemon.right,search_node), pokemon])
                        new_nodes.append(pokemon.right)
                    else:
                        dist = self.manhattan_distance(pokemon.right, search_node)
                        new_pokelist = sorted(new_pokelist, key = operator.itemgetter(0), reverse = True)
                        if new_pokelist[0][0] > dist:
                            new_pokelist[0] = [dist, pokemon.right]
                            new_nodes.append(pokemon.right)
                    #    else:  #descomentar para buscar todo el arbol
                       #     new_nodes.append(pokemon.right)
            nodes_to_check = new_nodes
        return new_pokelist
                    

    def search_pokemon_by_id(self, id):
        print("Estadisticas de pokemon de id " + str(id) + ":")
        print(self.pokemons.iloc[id-1])
        
    def search_pokemon_by_name(self, name):
        print("Estadisticas de pokemon " + name + ":")
        poke = self.pokemons.loc[self.pokemons['Name'] == name]
        id =poke.values[0][0]
        print(self.pokemons.iloc[id-1])
        
    def search_k_closest_pokemons(self, id, k):
        start_time = time.time()
        searched_pokemon = None
        for pokemon in self.vectorized_pokemons:
            if id == pokemon[0]:
                searched_pokemon = PokeNode(pokemon[0], pokemon[1], pokemon[2:])
                print(pokemon[2:])
                pokelist = self.search_knp(searched_pokemon, k)
                
        
        poke_ids = []
        for poke in pokelist:
            poke_ids.append(poke[1].poke_id)
        for i in poke_ids:
            self.search_pokemon_by_id(i)
        print("--- %s seconds ---" % (time.time() - start_time))
        
    def search_k_closest_pokemons_vector(self, vector, k):
        node = PokeNode('Example', 'Example', vector)
        print(node.poke_data)
        pokelist = self.search_knp(node, k)        
        poke_ids = []
        for poke in pokelist:
            poke_ids.append(poke[1].poke_id)
        for i in poke_ids:
            self.search_pokemon_by_id(i)        
  
                                
poke_tree = Pokedex(7) #inicializa poketree de 45 dimensiones       
poke_tree.pokemons = pokemon_db
poke_tree.vectorized_pokemons = poke_list
for pokemon in poke_list:
    pokenode = PokeNode(pokemon[0], pokemon[1], pokemon[2:])
    poke_tree.insert(pokenode)

a = poke_tree.root   



