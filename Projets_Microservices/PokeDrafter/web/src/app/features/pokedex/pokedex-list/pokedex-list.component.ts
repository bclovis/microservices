import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PokemonCardComponent } from '../../../shared/components/pokemon-card/pokemon-card.component';
import { InputComponent } from '../../../shared/components/input/input.component';
import { FormsModule } from '@angular/forms';
import { PokedexService } from '../../../core/services/pokedex.service';
import { Subject, debounceTime, distinctUntilChanged, switchMap, forkJoin, map, of, catchError } from 'rxjs';

@Component({
  selector: 'app-pokedex-list',
  standalone: true,
  imports: [CommonModule, PokemonCardComponent, InputComponent, FormsModule],
  template: `
    <div class="w-full h-full flex flex-col animate-fade-in">
      <div class="mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tight">Pokédex</h1>
          <p class="text-gray-500 text-sm">Browse and discover Pokémon data</p>
        </div>
        <div class="w-full md:w-96">
           <app-input 
             label="" 
             placeholder="Search Pokémon..." 
             [(ngModel)]="searchQuery" 
             (ngModelChange)="onSearchChange()"
             name="search" 
             class="light-theme-input">
           </app-input>
        </div>
      </div>

      <div *ngIf="loading && pokemons.length === 0" class="flex justify-center items-center py-20">
         <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-poke-blue"></div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 pb-8 place-items-center">
        <app-pokemon-card 
          *ngFor="let p of pokemons"
          [number]="p.number"
          [name]="p.name"
          [points]="p.points"
          [spriteUrl]="p.spriteUrl"
          [types]="p.types">
        </app-pokemon-card>
      </div>

      <div *ngIf="pokemons.length === 0 && !loading" class="text-center text-gray-500 py-12">
         No Pokémon found matching your search.
      </div>

      <div *ngIf="hasMore && !searchQuery" class="flex justify-center pb-12">
         <button 
            (click)="loadPokemon()" 
            [disabled]="loading"
            class="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-bold rounded-full shadow-sm hover:shadow-md hover:bg-gray-50 transition-all duration-200 disabled:opacity-50">
            {{ loading ? 'LOADING...' : 'LOAD MORE' }}
         </button>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    .animate-fade-in { animation: fadeIn 0.5s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    :host ::ng-deep .light-theme-input input {
      background-color: #ffffff !important;
      border: 1px solid #E5E7EB !important;
      color: #1F2937 !important;
      border-radius: 9999px !important;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
  `]
})
export class PokedexListComponent implements OnInit {
  searchQuery = '';
  private searchSubject = new Subject<string>();
  
  pokemons: any[] = [];
  loading = false;
  offset = 0;
  limit = 20;
  hasMore = true;

  constructor(private pokedexService: PokedexService) {}

  ngOnInit() {
    this.loadPokemon();

    this.searchSubject.pipe(
      debounceTime(400),
      distinctUntilChanged(),
      switchMap(query => {
        this.loading = true;
        if (!query) {
           this.offset = 0;
           this.pokemons = [];
           this.hasMore = true;
           return this.pokedexService.getPokemonList(this.offset, this.limit).pipe(
              switchMap(res => {
                 this.hasMore = !!res.next;
                 const detailRequests = res.results.map(p => this.pokedexService.getPokemonDetail(p.name));
                 return detailRequests.length ? forkJoin(detailRequests) : of([]);
              }),
              catchError(() => of([]))
           );
        }
        return this.pokedexService.searchPokemon(query).pipe(
           switchMap(results => {
              this.hasMore = false;
              const detailRequests = results.map(p => this.pokedexService.getPokemonDetail(p.name));
              return detailRequests.length ? forkJoin(detailRequests) : of([]);
           }),
           catchError(() => of([]))
        );
      })
    ).subscribe(details => {
       this.pokemons = this.formatPokemonDetails(details);
       this.loading = false;
    });
  }

  onSearchChange() {
    this.searchSubject.next(this.searchQuery);
  }

  loadPokemon() {
    if (this.loading && this.pokemons.length > 0) return;
    this.loading = true;
    this.pokedexService.getPokemonList(this.offset, this.limit).pipe(
      switchMap(res => {
        this.hasMore = !!res.next;
        const detailRequests = res.results.map(p => this.pokedexService.getPokemonDetail(p.name));
        return detailRequests.length ? forkJoin(detailRequests) : of([]);
      }),
      catchError(() => of([]))
    ).subscribe(details => {
      this.pokemons = [...this.pokemons, ...this.formatPokemonDetails(details)];
      this.offset += this.limit;
      this.loading = false;
    });
  }

  private formatPokemonDetails(details: any[]) {
     return details.map(d => ({
        number: d.id,
        name: d.name.charAt(0).toUpperCase() + d.name.slice(1),
        points: d.base_experience || 0,
        spriteUrl: d.sprites?.other?.['official-artwork']?.front_default || d.sprites?.front_default,
        types: d.types.map((t: any) => t.type.name.charAt(0).toUpperCase() + t.type.name.slice(1))
     }));
  }
}
