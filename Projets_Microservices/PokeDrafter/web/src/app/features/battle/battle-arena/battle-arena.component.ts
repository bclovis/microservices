import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService, User } from '../../../core/services/auth.service';
import { TeamService, Team } from '../../../core/services/team.service';
import { BattleService, Battle } from '../../../core/services/battle.service';
import { WebsocketService, ChatMessage } from '../../../core/services/websocket.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-battle-arena',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="w-full h-full flex flex-col animate-fade-in max-w-7xl mx-auto">
      <!-- Top Header -->
      <div class="mb-6 flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tight">Battle Arena</h1>
          <p class="text-gray-500 text-sm">Challenge opponents and rise through the ranks</p>
        </div>
        <div *ngIf="battle" class="px-4 py-2 bg-red-100 text-red-600 rounded-full text-xs font-black uppercase tracking-widest animate-pulse">
          LIVE MATCH
        </div>
      </div>

      <!-- Main Area -->
      <div class="flex-1 min-h-0 pb-6">
        
        <!-- Battle Field -->
        <div class="flex flex-col gap-6 h-full">
          
          <!-- Match Setup (if not in battle) -->
          <div *ngIf="!battle" class="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center flex-1">
             <div class="w-24 h-24 bg-poke-blue/10 rounded-full flex items-center justify-center mb-6">
                <svg class="w-12 h-12 text-poke-blue" fill="currentColor" viewBox="0 0 16 16">
                   <path d="M3.68 4.031c1.013 0 1.582-.57 1.582-1.582 0-1.013-.57-1.583-1.582-1.583-1.013 0-1.583.57-1.583 1.583S2.667 4.03 3.68 4.03Zm7.32 0.783a.75.75 0 1 0 1.5-.06 49.983 49.983 0 0 0-.049-.971A2.652 2.652 0 0 0 9.96 1.29c-.5-.03-.994-.05-1.487-.065a.75.75 0 1 0-.043 1.5c.477.013.957.034 1.441.063a1.152 1.152 0 0 1 1.084 1.083c.018.317.034.63.046.943Zm-5.605 8.244a.75.75 0 0 0 .046-1.499c-.45-.014-.904-.034-1.361-.061a1.152 1.152 0 0 1-1.084-1.084 48.78 48.78 0 0 1-.023-.424.75.75 0 0 0-1.498.076l.024.437a2.652 2.652 0 0 0 2.492 2.492c.472.028.94.05 1.404.063Zm4.925-2.675c1.303 0 2.197.91 2.382 2.178.04.273-.189.498-.465.498H8.402c-.276 0-.505-.225-.465-.498 0.185-1.269 1.078-2.178 2.382-2.178Zm-4.258-3.5C5.878 5.616 4.984 4.707 3.68 4.707s-2.198.91-2.383 2.178c-.04.273.189.498.465.498h3.836c.276 0 .504-.225.464-.498Zm5.84 1.244c0 1.013-.57 1.583-1.583 1.583s-1.582-.57-1.582-1.583 0.57-1.583 1.582-1.583c1.013 0 1.583 0.57 1.583 1.583Z"/>
                </svg>
             </div>
             <h2 class="text-2xl font-black text-gray-800 uppercase mb-2">Ready to Fight?</h2>
             <p class="text-gray-500 mb-8 max-w-md text-center italic">Choose your team and join the queue to find an opponent.</p>
             
             <div class="w-full max-w-sm space-y-4">
                <div class="space-y-2">
                   <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Your Team</label>
                   <select [(ngModel)]="selectedTeamId" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-poke-blue transition-all outline-none text-gray-700 font-bold">
                      <option [value]="null">Select a team...</option>
                      <option *ngFor="let t of myTeams" [value]="t.id">{{ t.name }}</option>
                   </select>
                </div>
                
                <button 
                   [disabled]="!selectedTeamId || loading"
                   (click)="startMatchmaking()"
                   class="w-full py-4 bg-poke-blue hover:bg-poke-blue-dark text-white font-black rounded-2xl shadow-xl transform hover:scale-[1.02] active:scale-[0.98] transition-all uppercase tracking-widest disabled:opacity-50">
                   {{ loading ? 'Finding Opponent...' : 'Join Queue' }}
                </button>
             </div>
          </div>

          <!-- Active Battle Arena -->
          <div *ngIf="battle" class="flex-1 flex flex-col gap-6">
             <!-- Scoreboard -->
             <div class="bg-gray-900 rounded-3xl p-6 flex justify-between items-center text-white shadow-2xl relative overflow-hidden border-4 border-gray-800">
                <div class="flex items-center gap-4 relative z-10">
                   <div class="w-12 h-12 rounded-full border-2 border-red-500 bg-red-500/20 flex items-center justify-center font-black">R</div>
                   <div>
                      <div class="text-[10px] text-gray-400 font-black uppercase tracking-widest">Player Red</div>
                      <div class="font-bold">{{ currentUser?.username }}</div>
                   </div>
                </div>

                <div class="flex flex-col items-center relative z-10">
                   <div class="text-4xl font-black italic tracking-tighter">
                      {{ scoreRed }} — {{ scoreBlue }}
                   </div>
                   <div class="text-[8px] font-black text-poke-blue uppercase tracking-[0.3em] mt-1">ROUND {{ battle.current_turn + 1 }}</div>
                </div>

                <div class="flex items-center gap-4 text-right relative z-10">
                   <div>
                      <div class="text-[10px] text-gray-400 font-black uppercase tracking-widest">Player Blue</div>
                      <div class="font-bold">Opponent</div>
                   </div>
                   <div class="w-12 h-12 rounded-full border-2 border-blue-500 bg-blue-500/20 flex items-center justify-center font-black">B</div>
                </div>
                
                <!-- Background decorative elements -->
                <div class="absolute inset-0 bg-gradient-to-r from-red-900/20 via-transparent to-blue-900/20"></div>
             </div>

             <!-- Battle Field -->
             <div class="flex-1 bg-white rounded-3xl border border-gray-100 shadow-sm p-8 flex flex-col justify-between relative overflow-hidden min-h-[400px]">
                <div class="flex justify-between items-center mb-12">
                   <!-- Opponent Active Pokemon -->
                   <div class="flex flex-col items-center">
                      <div class="w-32 h-32 bg-gray-50 rounded-full flex items-center justify-center border-4 border-blue-100 relative shadow-inner">
                         <img *ngIf="opponentActivePokemon" [src]="getSpriteUrl(opponentActivePokemon.id)" class="w-24 h-24 object-contain animate-bounce-subtle">
                         <div *ngIf="!opponentActivePokemon" class="text-gray-300">?</div>
                         <!-- HP Bar -->
                         <div class="absolute -top-4 w-full px-2">
                            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                               <div class="h-full bg-blue-500 w-full transition-all"></div>
                            </div>
                         </div>
                      </div>
                      <div class="mt-2 text-sm font-bold text-gray-400 uppercase tracking-widest">Opponent</div>
                   </div>

                   <!-- VS Logo -->
                   <div class="w-16 h-16 bg-poke-blue text-white rounded-full flex items-center justify-center font-black italic text-2xl shadow-lg z-10">VS</div>

                   <!-- Player Active Pokemon -->
                   <div class="flex flex-col items-center">
                      <div class="w-40 h-40 bg-gray-50 rounded-full flex items-center justify-center border-4 border-red-100 relative shadow-inner">
                         <img *ngIf="activePokemon" [src]="getSpriteUrl(activePokemon.pokemon_id)" class="w-32 h-32 object-contain animate-float">
                         <div *ngIf="!activePokemon" class="text-gray-300">Select</div>
                         <!-- HP Bar -->
                         <div class="absolute -top-4 w-full px-2">
                            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                               <div class="h-full bg-green-500 w-full transition-all"></div>
                            </div>
                         </div>
                      </div>
                      <div class="mt-2 text-sm font-bold text-gray-800 uppercase tracking-widest">You</div>
                   </div>
                </div>

                <!-- Action Controls -->
                <div class="bg-gray-50 rounded-2xl p-4 border border-gray-100 max-w-2xl mx-auto w-full">
                   <div class="flex justify-between items-center mb-3">
                      <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Your Squad</span>
                      <span class="text-[10px] font-black text-poke-blue uppercase tracking-widest">Select to Move</span>
                   </div>
                   <div class="flex gap-4 overflow-x-auto pb-2 justify-center">
                      <div *ngFor="let p of currentTeam?.pokemon" 
                           (click)="selectPokemon(p)"
                           [class.border-poke-blue]="activePokemon?.pokemon_id === p.pokemon_id"
                           class="w-16 h-16 bg-white rounded-xl flex-shrink-0 flex items-center justify-center border-2 border-transparent hover:border-poke-blue transition-all cursor-pointer p-2 shadow-sm">
                         <img [src]="getSpriteUrl(p.pokemon_id)" class="w-full h-full object-contain">
                      </div>
                   </div>
                   
                   <button 
                      [disabled]="!activePokemon || turnProcessing"
                      (click)="playTurn()"
                      class="w-full mt-4 py-4 bg-gray-900 hover:bg-black text-white font-black rounded-xl uppercase tracking-widest transition-all disabled:opacity-50">
                      {{ turnProcessing ? 'Resolving...' : 'Attack!' }}
                   </button>
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
    @keyframes float { 
       0% { transform: translateY(0px); }
       50% { transform: translateY(-10px); }
       100% { transform: translateY(0px); }
    }
    @keyframes bounce-subtle {
       0%, 100% { transform: translateY(0); }
       50% { transform: translateY(-5px); }
    }
    .animate-float { animation: float 3s ease-in-out infinite; }
    .animate-bounce-subtle { animation: bounce-subtle 2s ease-in-out infinite; }
  `]
})
export class BattleArenaComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  myTeams: Team[] = [];
  selectedTeamId: string | null = null;
  currentTeam: Team | null = null;
  
  battle: Battle | null = null;
  activePokemon: any = null;
  opponentActivePokemon: any = null;
  scoreRed = 0;
  scoreBlue = 0;
  
  loading = false;
  turnProcessing = false;
  
  private subs = new Subscription();

  constructor(
    private authService: AuthService,
    private teamService: TeamService,
    private battleService: BattleService,
    private wsService: WebsocketService
  ) {}

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => this.currentUser = user);
    this.loadTeams();
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
  }

  loadTeams() {
    this.teamService.listTeams().subscribe(teams => {
      this.myTeams = teams;
    });
  }

  startMatchmaking() {
    if (!this.selectedTeamId || !this.currentUser) return;
    
    this.loading = true;
    this.currentTeam = this.myTeams.find(t => t.id === this.selectedTeamId) || null;

    // Simulate finding an opponent
    setTimeout(() => {
      this.battleService.createBattle({
        player_red_id: this.currentUser!.id,
        player_blue_id: '00000000-0000-0000-0000-000000000000', // Bot
        mode: 'standard'
      }).subscribe(battle => {
        this.battle = battle;
        this.loading = false;
        
        // Pick first pokemon as active
        if (this.currentTeam?.pokemon.length) {
          this.activePokemon = this.currentTeam.pokemon[0];
        }
        
        // Mock opponent pokemon
        this.opponentActivePokemon = { id: Math.floor(Math.random() * 150) + 1 };
      });
    }, 1500);
  }

  selectPokemon(p: any) {
    if (this.turnProcessing) return;
    this.activePokemon = p;
  }

  playTurn() {
    if (!this.battle || !this.activePokemon || this.turnProcessing) return;
    
    this.turnProcessing = true;
    
    this.battleService.playTurn(this.battle.id, {
      pokemon_red: this.activePokemon.pokemon_name,
      pokemon_blue: 'Mewtwo', // Mock opponent
      types_red: [this.activePokemon.type1, ...(this.activePokemon.type2 ? [this.activePokemon.type2] : [])],
      types_blue: ['Psychic']
    }).subscribe({
      next: (result) => {
        this.turnProcessing = false;
        if (result.result === 'A') this.scoreRed++;
        if (result.result === 'B') this.scoreBlue++;
        
        this.battle!.current_turn++;
        
        // Mock next opponent pokemon
        this.opponentActivePokemon = { id: Math.floor(Math.random() * 150) + 1 };
      },
      error: () => {
        this.turnProcessing = false;
      }
    });
  }

  getSpriteUrl(pokemonId: number | string): string {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemonId}.png`;
  }
}
