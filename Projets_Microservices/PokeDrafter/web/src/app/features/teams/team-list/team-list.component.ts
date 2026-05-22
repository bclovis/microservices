import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { TeamService, Team } from '../../../core/services/team.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-team-list',
  standalone: true,
  imports: [CommonModule, ButtonComponent],
  template: `
    <div class="w-full h-full flex flex-col animate-fade-in">
      <div class="mb-8 flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tight">My Teams</h1>
          <p class="text-gray-500 text-sm">Manage your pre-constructed teams</p>
        </div>
        <button 
          class="px-6 py-2 bg-poke-blue hover:bg-poke-blue-dark text-white font-bold rounded-full shadow-lg transform hover:scale-105 transition-all duration-200 uppercase tracking-wide text-sm"
          (click)="createNewTeam()">
          + New Team
        </button>
      </div>

      <div *ngIf="loading" class="flex justify-center items-center py-20">
         <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-poke-blue"></div>
      </div>

      <div *ngIf="!loading && teams.length === 0" class="text-center text-gray-500 py-12 bg-white rounded-2xl border-2 border-dashed border-gray-200">
         <p class="text-lg font-medium mb-4">You haven't created any teams yet.</p>
         <button 
           class="px-6 py-2 bg-poke-blue text-white font-bold rounded-full"
           (click)="createNewTeam()">
           Build your first team
         </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 pb-12">
        <div *ngFor="let team of teams" class="bg-white rounded-2xl shadow-md border-2 border-gray-100 p-6 flex flex-col hover:shadow-xl transition-shadow cursor-pointer hover:border-poke-blue/30">
          <div class="flex justify-between items-center mb-4">
             <h3 class="text-xl font-bold text-gray-800">{{ team.name }}</h3>
          </div>
          
          <!-- Miniature Team Display -->
          <div class="grid grid-cols-3 gap-2 mb-4">
            <div *ngFor="let p of team.pokemon" class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center border border-gray-200 p-2" [title]="p.pokemon_name">
              <img [src]="getSpriteUrl(p.pokemon_id)" [alt]="p.pokemon_name" class="w-full h-full object-contain">
            </div>
            <!-- Empty slots if any -->
            <div *ngFor="let _ of [].constructor(6 - team.pokemon.length)" class="w-16 h-16 bg-gray-50 rounded-full border border-dashed border-gray-300 flex items-center justify-center">
               <span class="text-gray-400 text-xs">+</span>
            </div>
          </div>
          
          <div class="mt-auto flex justify-between items-center pt-4 border-t border-gray-100">
             <span class="text-xs text-gray-500 font-medium">Created: {{ team.created_at | date:'shortDate' }}</span>
             <div class="flex gap-4">
                <button (click)="deleteTeam(team.id, $event)" class="text-xs font-bold text-red-500 hover:text-red-700 uppercase">Delete</button>
                <button (click)="editTeam(team.id)" class="text-xs font-bold text-poke-blue hover:text-poke-blue-dark uppercase">Edit</button>
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
  `]
})
export class TeamListComponent implements OnInit {
  teams: Team[] = [];
  loading = false;

  constructor(
    private teamService: TeamService,
    private router: Router
  ) { }

  ngOnInit() {
    this.loadTeams();
  }

  loadTeams() {
    this.loading = true;
    this.teamService.listTeams().subscribe({
      next: (teams) => {
        this.teams = teams;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading teams', err);
        this.loading = false;
      }
    });
  }

  createNewTeam() {
    this.router.navigate(['/dashboard/teams/build']);
  }

  editTeam(id: string) {
    this.router.navigate(['/dashboard/teams/build'], { queryParams: { id } });
  }

  deleteTeam(id: string, event: MouseEvent) {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this team?')) {
      this.teamService.deleteTeam(id).subscribe(() => {
        this.loadTeams();
      });
    }
  }

  getSpriteUrl(pokemonId: number): string {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemonId}.png`;
  }
}

