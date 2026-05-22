import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TeamService, TeamPokemon } from '../../../core/services/team.service';
import { PokedexService } from '../../../core/services/pokedex.service';
import { InputComponent } from '../../../shared/components/input/input.component';
import { Subject, debounceTime, distinctUntilChanged, switchMap, forkJoin, of, catchError } from 'rxjs';

@Component({
  selector: 'app-team-builder',
  standalone: true,
  imports: [CommonModule, FormsModule, InputComponent],
  template: `
    <div class="w-full h-full flex flex-col animate-fade-in max-w-6xl mx-auto">
      <div class="mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tight">
            {{ isEditing ? 'Edit Team' : 'Build New Team' }}
          </h1>
          <p class="text-gray-500 text-sm">Assemble your ultimate squad of 6 Pokémon</p>
        </div>
        <div class="flex gap-4">
          <button 
            *ngIf="isEditing"
            [disabled]="completing"
            (click)="completeTeam()" 
            class="px-6 py-2 bg-purple-100 text-purple-600 font-bold rounded-full hover:bg-purple-200 transition-all uppercase tracking-wide text-sm flex items-center gap-2">
            <svg *ngIf="!completing" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
            <div *ngIf="completing" class="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            {{ completing ? 'Completing...' : 'AI Complete' }}
          </button>
          <button (click)="goBack()" class="px-6 py-2 bg-gray-100 text-gray-600 font-bold rounded-full hover:bg-gray-200 transition-all uppercase tracking-wide text-sm">
            Cancel
          </button>
          <button 
            [disabled]="!isValid() || saving"
            (click)="saveTeam()" 
            class="px-8 py-2 bg-poke-blue hover:bg-poke-blue-dark text-white font-bold rounded-full shadow-lg transform hover:scale-105 transition-all duration-200 uppercase tracking-wide text-sm disabled:opacity-50 disabled:transform-none">
            {{ saving ? 'Saving...' : 'Save Team' }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 pb-12">
        <!-- Left: Team Name and Slots -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <app-input 
              label="Team Name" 
              placeholder="e.g. My Competitive Squad" 
              [(ngModel)]="teamName" 
              name="teamName"
              class="light-theme-input mb-6">
            </app-input>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div *ngFor="let slot of [1,2,3,4,5,6]" 
                   (click)="selectSlot(slot)"
                   [class.ring-2]="activeSlot === slot"
                   [class.ring-poke-blue]="activeSlot === slot"
                   class="aspect-square bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center p-4 cursor-pointer hover:bg-gray-100 transition-all group relative">
                
                <ng-container *ngIf="getPokemonInSlot(slot) as p; else emptySlot">
                  <img [src]="getSpriteUrl(p.pokemon_id)" [alt]="p.pokemon_name" class="w-20 h-20 object-contain mb-2">
                  <span class="text-xs font-bold text-gray-800 text-center uppercase truncate w-full">{{ p.pokemon_name }}</span>
                  <button (click)="removePokemon(slot, $event)" class="absolute top-2 right-2 w-6 h-6 bg-red-100 text-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-200">
                    ×
                  </button>
                </ng-container>

                <ng-template #emptySlot>
                  <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-400 mb-2">
                    <span class="text-xl">+</span>
                  </div>
                  <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Slot {{ slot }}</span>
                </ng-template>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Search and Selection -->
        <div class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-[600px] flex flex-col">
            <h3 class="text-lg font-bold text-gray-800 mb-4 uppercase tracking-tight">Select Pokémon</h3>
            <div class="relative mb-4">
              <app-input 
                label="" 
                placeholder="Search..." 
                [(ngModel)]="searchQuery" 
                (ngModelChange)="onSearchChange()"
                name="search" 
                class="light-theme-input">
              </app-input>
            </div>

            <div class="flex-1 overflow-y-auto pr-2 space-y-2">
              <div *ngIf="searching" class="flex justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-poke-blue"></div>
              </div>

              <div *ngFor="let p of searchResults" 
                   (click)="addPokemonToActiveSlot(p)"
                   class="flex items-center gap-4 p-2 rounded-xl hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-100 transition-all group">
                <div class="w-12 h-12 bg-gray-100 rounded-lg p-1 group-hover:scale-110 transition-transform">
                  <img [src]="getSpriteUrl(p.id)" [alt]="p.name" class="w-full h-full object-contain">
                </div>
                <div>
                  <h4 class="text-sm font-bold text-gray-800 capitalize">{{ p.name }}</h4>
                  <div class="flex gap-1">
                    <span *ngFor="let t of p.types" class="text-[8px] font-black uppercase px-1.5 py-0.5 rounded-full border border-gray-200 text-gray-500">
                      {{ t }}
                    </span>
                  </div>
                </div>
              </div>

              <div *ngIf="!searching && searchResults.length === 0 && searchQuery" class="text-center text-gray-400 py-8 text-sm">
                No results for "{{ searchQuery }}"
              </div>

              <div *ngIf="!searchQuery && !searching" class="text-center text-gray-400 py-8 text-sm">
                Search to find Pokémon
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; }
    .animate-fade-in { animation: fadeIn 0.5s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    :host ::ng-deep .light-theme-input input {
      background-color: #f9fafb !important;
      border: 1px solid #E5E7EB !important;
      color: #1F2937 !important;
      border-radius: 12px !important;
    }
  `]
})
export class TeamBuilderComponent implements OnInit {
  teamName = '';
  selectedPokemon: TeamPokemon[] = [];
  activeSlot: number = 1;
  searchQuery = '';
  searchResults: any[] = [];
  searching = false;
  saving = false;
  isEditing = false;
  teamId: string | null = null;
  completing = false;

  private searchSubject = new Subject<string>();

  constructor(
    private pokedexService: PokedexService,
    private teamService: TeamService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['id']) {
        this.isEditing = true;
        this.teamId = params['id'];
        this.loadTeam(this.teamId!);
      }
    });

    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (!query) {
          this.searchResults = [];
          return of([]);
        }
        this.searching = true;
        return this.pokedexService.searchPokemon(query).pipe(
          switchMap(results => {
            const detailRequests = results.map(p => this.pokedexService.getPokemonDetail(p.name));
            return detailRequests.length ? forkJoin(detailRequests) : of([]);
          }),
          catchError(() => of([]))
        );
      })
    ).subscribe(details => {
      this.searchResults = details.map(d => ({
        id: d.id,
        name: d.name,
        types: d.types.map((t: any) => t.type.name)
      }));
      this.searching = false;
    });
  }

  loadTeam(id: string) {
    this.teamService.getTeam(id).subscribe(team => {
      this.teamName = team.name;
      this.selectedPokemon = [...team.pokemon];
    });
  }

  onSearchChange() {
    this.searchSubject.next(this.searchQuery);
  }

  selectSlot(slot: number) {
    this.activeSlot = slot;
  }

  getPokemonInSlot(slot: number): TeamPokemon | undefined {
    return this.selectedPokemon.find(p => p.slot === slot);
  }

  addPokemonToActiveSlot(pokemon: any) {
    const existingIndex = this.selectedPokemon.findIndex(p => p.slot === this.activeSlot);
    const newPokemon: TeamPokemon = {
      pokemon_id: pokemon.id,
      pokemon_name: pokemon.name,
      type1: pokemon.types[0],
      type2: pokemon.types[1] || undefined,
      slot: this.activeSlot
    };

    if (existingIndex > -1) {
      this.selectedPokemon[existingIndex] = newPokemon;
    } else {
      this.selectedPokemon.push(newPokemon);
    }

    // Auto-advance to next slot if empty
    if (this.activeSlot < 6) {
      this.activeSlot++;
    }
  }

  removePokemon(slot: number, event: MouseEvent) {
    event.stopPropagation();
    this.selectedPokemon = this.selectedPokemon.filter(p => p.slot !== slot);
  }

  isValid() {
    return this.teamName.trim().length > 0 && this.selectedPokemon.length > 0;
  }

  saveTeam() {
    if (!this.isValid()) return;
    this.saving = true;

    const payload = {
      name: this.teamName,
      pokemon: this.selectedPokemon
    };

    const obs = this.isEditing && this.teamId
      ? this.teamService.updateTeam(this.teamId, payload)
      : this.teamService.createTeam(payload);

    obs.subscribe({
      next: () => {
        this.router.navigate(['/dashboard/teams']);
      },
      error: (err) => {
        console.error('Error saving team', err);
        this.saving = false;
      }
    });
  }

  goBack() {
    this.router.navigate(['/dashboard/teams']);
  }

  completeTeam() {
    if (!this.teamId) return;
    this.completing = true;
    this.teamService.completeTeam(this.teamId).subscribe({
      next: (team) => {
        this.selectedPokemon = [...team.pokemon];
        this.completing = false;
      },
      error: (err) => {
        console.error('Error completing team', err);
        this.completing = false;
      }
    });
  }

  getSpriteUrl(pokemonId: number): string {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemonId}.png`;
  }
}
