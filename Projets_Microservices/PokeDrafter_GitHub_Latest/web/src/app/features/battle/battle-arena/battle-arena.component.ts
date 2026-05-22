import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService, User } from '../../../core/services/auth.service';
import { TeamService, Team } from '../../../core/services/team.service';
import { BattleService, Battle } from '../../../core/services/battle.service';
import { WebsocketService, ChatMessage } from '../../../core/services/websocket.service';
import { PokedexService } from '../../../core/services/pokedex.service';
import { BattleTimerComponent } from '../battle-timer/battle-timer.component';
import { Subscription, firstValueFrom } from 'rxjs';

type BattlePhase = 'selection' | 'drafting' | 'battle' | 'finished';
type BattleMode = 'constructed' | 'random' | 'draft';

@Component({
  selector: 'app-battle-arena',
  standalone: true,
  imports: [CommonModule, FormsModule, BattleTimerComponent],
  template: `
    <div class="w-full h-full flex flex-col animate-fade-in max-w-7xl mx-auto p-4 md:p-6 gap-6">
      
      <!-- Top Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tight">Battle Arena</h1>
          <p class="text-gray-500 text-sm">
            <span *ngIf="phase === 'selection'">Choose your game mode and prepare for battle</span>
            <span *ngIf="phase === 'drafting'">Drafting Phase: Choose your team carefully</span>
            <span *ngIf="phase === 'battle'">Battle in progress — Good luck!</span>
          </p>
        </div>
        <div *ngIf="phase === 'battle'" class="px-4 py-2 bg-red-100 text-red-600 rounded-full text-xs font-black uppercase tracking-widest animate-pulse">
          LIVE MATCH
        </div>
      </div>

      <div class="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
        
        <!-- Main Game Area -->
        <div class="lg:col-span-4 flex flex-col gap-6">
          
          <!-- PHASE: SELECTION -->
          <div *ngIf="phase === 'selection'" class="flex-1 bg-white rounded-3xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center">
             <div class="w-20 h-20 bg-poke-blue/10 rounded-full flex items-center justify-center mb-6">
                <svg class="w-10 h-10 text-poke-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
             </div>
             <h2 class="text-2xl font-black text-gray-800 uppercase mb-2">Ready to Fight?</h2>
             <p class="text-gray-500 mb-8 max-w-md text-center italic">Select a battle mode and prepare your team.</p>
             
             <div class="w-full max-w-2xl grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- Draft Mode -->
                <button (click)="selectMode('draft')" class="p-6 bg-gray-50 rounded-2xl border-2 hover:border-poke-blue transition-all text-center group" [class.border-poke-blue]="selectedMode === 'draft'" [class.border-transparent]="selectedMode !== 'draft'">
                   <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:scale-110 transition-transform">
                      <svg class="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16m-7 6h7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                   </div>
                   <h3 class="font-black uppercase text-xs tracking-widest mb-1">Draft</h3>
                   <p class="text-[10px] text-gray-400">Pick from random pool</p>
                </button>

                <!-- Constructed Mode -->
                <button (click)="selectMode('constructed')" class="p-6 bg-gray-50 rounded-2xl border-2 hover:border-poke-blue transition-all text-center group" [class.border-poke-blue]="selectedMode === 'constructed'" [class.border-transparent]="selectedMode !== 'constructed'">
                   <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:scale-110 transition-transform">
                      <svg class="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                   </div>
                   <h3 class="font-black uppercase text-xs tracking-widest mb-1">Constructed</h3>
                   <p class="text-[10px] text-gray-400">Use your own team</p>
                </button>

                <!-- Hazard Mode -->
                <button (click)="selectMode('random')" class="p-6 bg-gray-50 rounded-2xl border-2 hover:border-poke-blue transition-all text-center group" [class.border-poke-blue]="selectedMode === 'random'" [class.border-transparent]="selectedMode !== 'random'">
                   <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:scale-110 transition-transform">
                      <svg class="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a2 2 0 00-1.96 1.414l-.477 2.387a2 2 0 00.547 1.022l1.428 1.428a2 2 0 001.414.586H19a2 2 0 002-2v-1.172a2 2 0 00-.586-1.414l-1.428-1.428zM9.003 10.997a3 3 0 11-6 0 3 3 0 016 0zm0 0h3.017M9 21h3m9-9h-3m-1.427-6.573a2 2 0 01-1.022-.547L17.164 4.5a2 2 0 011.414-.586H20a2 2 0 012 2v1.172a2 2 0 01-.586 1.414l-1.428 1.428a2 2 0 01-1.022.547l-2.387.477a2 2 0 01-1.96-1.414l-.477-2.387zM9 9l3 3m0 0l3-3m-3 3l-3 3m3-3l3 3" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                   </div>
                   <h3 class="font-black uppercase text-xs tracking-widest mb-1">Hazard</h3>
                   <p class="text-[10px] text-gray-400">Randomized teams</p>
                </button>
             </div>

             <div *ngIf="selectedMode === 'constructed'" class="w-full max-w-sm mt-8 space-y-2 animate-slide-up">
                <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Select Your Team</label>
                <select [(ngModel)]="selectedTeamId" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-poke-blue transition-all outline-none text-gray-700 font-bold">
                   <option [value]="null">Select a team...</option>
                   <option *ngFor="let t of myTeams" [value]="t.id">{{ t.name }}</option>
                </select>
             </div>

             <button 
                [disabled]="(selectedMode === 'constructed' && !selectedTeamId) || loading || !selectedMode"
                (click)="startMatchmaking()"
                class="mt-10 px-12 py-4 bg-gray-900 hover:bg-black text-white font-black rounded-2xl shadow-xl transform hover:scale-[1.02] active:scale-[0.98] transition-all uppercase tracking-widest disabled:opacity-50">
                {{ loading ? 'Finding Opponent...' : 'Start Match' }}
             </button>

             <div *ngIf="errorMessage" class="mt-4 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-xs font-bold">
                {{ errorMessage }}
             </div>
          </div>

          <!-- PHASE: DRAFTING -->
          <div *ngIf="phase === 'drafting'" class="flex-1 bg-white rounded-3xl shadow-sm border border-gray-100 p-8 flex flex-col">
             <div class="flex justify-between items-center mb-8">
                <div>
                   <h2 class="text-xl font-black text-gray-800 uppercase tracking-tight">Drafting Pool</h2>
                   <p class="text-xs text-gray-400 uppercase font-black tracking-widest mt-1">
                      {{ isRedTurn ? 'Player Red' : 'Player Blue' }}'s Turn to Pick
                   </p>
                </div>
                <div class="flex gap-4">
                   <div class="flex flex-col items-center">
                      <span class="text-[8px] font-black uppercase text-red-500 mb-1">Red</span>
                      <div class="flex -space-x-2">
                         <div *ngFor="let p of draftPicksRed" class="w-8 h-8 rounded-full bg-gray-100 border-2 border-white overflow-hidden shadow-sm">
                            <img [src]="getSpriteUrl(p.id)" class="w-full h-full object-contain">
                         </div>
                         <div *ngFor="let i of [1,2,3,4,5,6]" [class.hidden]="i <= draftPicksRed.length" class="w-8 h-8 rounded-full bg-gray-50 border-2 border-dashed border-gray-200"></div>
                      </div>
                   </div>
                   <div class="flex flex-col items-center">
                      <span class="text-[8px] font-black uppercase text-blue-500 mb-1">Blue</span>
                      <div class="flex -space-x-2">
                         <div *ngFor="let p of draftPicksBlue" class="w-8 h-8 rounded-full bg-gray-100 border-2 border-white overflow-hidden shadow-sm">
                            <img [src]="getSpriteUrl(p.id)" class="w-full h-full object-contain">
                         </div>
                         <div *ngFor="let i of [1,2,3,4,5,6]" [class.hidden]="i <= draftPicksBlue.length" class="w-8 h-8 rounded-full bg-gray-50 border-2 border-dashed border-gray-200"></div>
                      </div>
                   </div>
                </div>
             </div>

             <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 overflow-y-auto">
                <div *ngFor="let p of draftingPool" 
                     (click)="pickPokemon(p)"
                     class="group relative bg-gray-50 rounded-2xl p-4 border-2 transition-all cursor-pointer hover:border-poke-blue"
                     [class.opacity-30]="p.picked" [class.pointer-events-none]="p.picked">
                   <img [src]="getSpriteUrl(p.id)" class="w-full h-24 object-contain group-hover:scale-110 transition-transform">
                   <div class="mt-2 text-center">
                      <div class="text-[10px] font-black uppercase truncate">{{ p.name }}</div>
                      <div class="flex justify-center gap-1 mt-1">
                         <span *ngFor="let t of p.types" class="px-1.5 py-0.5 rounded text-[7px] font-bold text-white uppercase" [style.background-color]="getTypeColor(t)">{{ t }}</span>
                      </div>
                   </div>
                </div>
             </div>
          </div>

          <!-- PHASE: BATTLE -->
          <div *ngIf="phase === 'battle'" class="flex-1 flex flex-col gap-6 animate-fade-in">
             <!-- Scoreboard -->
             <div class="bg-gray-900 rounded-3xl p-6 flex justify-between items-center text-white shadow-2xl relative overflow-hidden border-4 border-gray-800">
                <div class="flex items-center gap-4 relative z-10">
                   <div class="w-12 h-12 rounded-full border-2 border-red-500 bg-red-500/20 flex items-center justify-center font-black">R</div>
                   <div>
                      <div class="text-[10px] text-gray-400 font-black uppercase tracking-widest">Player Red</div>
                      <div class="font-bold">{{ (battle?.player_red_id === currentUser?.id) ? currentUser?.username : 'Opponent' }}</div>
                   </div>
                </div>

                <div class="flex flex-col items-center relative z-10">
                   <div class="text-4xl font-black italic tracking-tighter">
                      {{ scoreRed }} — {{ scoreBlue }}
                   </div>
                   <div class="text-[8px] font-black text-poke-blue uppercase tracking-[0.3em] mt-1">ROUND {{ battle?.current_turn ? battle!.current_turn + 1 : 1 }}</div>
                </div>

                <div class="flex items-center gap-4 text-right relative z-10">
                   <div>
                      <div class="text-[10px] text-gray-400 font-black uppercase tracking-widest">Player Blue</div>
                      <div class="font-bold">{{ (battle?.player_blue_id === currentUser?.id) ? currentUser?.username : 'Opponent' }}</div>
                   </div>
                   <div class="w-12 h-12 rounded-full border-2 border-blue-500 bg-blue-500/20 flex items-center justify-center font-black">B</div>
                </div>
                
                <div class="absolute inset-0 bg-gradient-to-r from-red-900/20 via-transparent to-blue-900/20"></div>
             </div>

             <!-- Field -->
             <div class="flex-1 bg-white rounded-3xl border border-gray-100 shadow-sm p-8 flex flex-col justify-between relative overflow-hidden min-h-[450px]">
                
                <!-- Timer -->
                <div class="absolute top-4 right-4">
                   <app-battle-timer #timer (timeout)="onTimeout()"></app-battle-timer>
                </div>

                <!-- Opponent Side -->
                <div class="flex justify-between items-start">
                   <div class="flex flex-col items-center ml-20">
                      <div class="w-36 h-36 bg-gray-50 rounded-full flex items-center justify-center border-4 border-blue-100 relative shadow-inner">
                         <img *ngIf="opponentActivePokemon" [src]="getSpriteUrl(opponentActivePokemon.id)" class="w-28 h-28 object-contain animate-bounce-subtle">
                         <div *ngIf="!opponentActivePokemon" class="text-gray-300 font-black text-2xl">?</div>
                         <div class="absolute -top-4 w-full px-2">
                            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                               <div class="h-full bg-blue-500 w-full transition-all"></div>
                            </div>
                         </div>
                      </div>
                      <div class="mt-2 text-right">
                         <h4 class="text-[8px] font-black text-gray-300 uppercase tracking-widest">Enemy Active</h4>
                         <div *ngIf="opponentActivePokemon" class="text-sm font-black uppercase text-gray-800 tracking-tighter">{{ opponentActivePokemon.name }}</div>
                      </div>
                   </div>
                   
                   <div class="flex flex-col items-end mr-20 gap-2">
                      <span class="text-[8px] font-black text-gray-400 uppercase tracking-widest">Enemy Squad</span>
                      <div class="flex gap-2">
                         <div *ngFor="let p of opponentTeam" 
                              class="w-10 h-10 bg-gray-50 rounded-lg flex items-center justify-center border border-gray-100 overflow-hidden relative shadow-sm">
                            <img *ngIf="selectedMode !== 'random' || p.hasBeenSeen || p.isKO" [src]="getSpriteUrl(p.id)" class="w-8 h-8 object-contain">
                            <div *ngIf="selectedMode === 'random' && !p.hasBeenSeen && !p.isKO" class="text-gray-300 font-black text-xs">?</div>
                            <div *ngIf="p.isKO" class="absolute inset-0 bg-red-500/10 flex items-center justify-center">
                               <svg class="w-6 h-6 text-red-500/50" fill="currentColor" viewBox="0 0 20 20"><path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" fill-rule="evenodd"/></svg>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>

                <!-- Center VS -->
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                   <div class="w-20 h-20 bg-poke-blue text-white rounded-full flex items-center justify-center font-black italic text-3xl shadow-2xl z-10 border-8 border-white">VS</div>
                </div>

                <!-- Player Side -->
                <div class="flex justify-between items-end">
                   <div class="ml-32 pb-10">
                      <h4 class="text-xs font-black text-gray-300 uppercase tracking-widest">Your Active</h4>
                      <div *ngIf="activePokemon" class="text-xl font-black uppercase text-gray-800 tracking-tighter">{{ activePokemon.name || activePokemon.pokemon_name }}</div>
                   </div>

                   <div class="flex flex-col items-center mr-20">
                      <div class="w-44 h-44 bg-gray-50 rounded-full flex items-center justify-center border-4 border-red-100 relative shadow-inner">
                         <img *ngIf="activePokemon" [src]="getSpriteUrl(activePokemon.id || activePokemon.pokemon_id)" class="w-36 h-36 object-contain animate-float">
                         <div *ngIf="!activePokemon" class="text-gray-300 font-black text-2xl">?</div>
                         <div class="absolute -top-4 w-full px-2">
                            <div class="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                               <div class="h-full bg-green-500 w-full transition-all"></div>
                            </div>
                         </div>
                      </div>
                      <div class="mt-2 flex gap-1">
                         <div *ngFor="let p of playerTeam" class="w-4 h-4 rounded-full border border-white" [class.bg-red-500]="!p.isKO" [class.bg-gray-300]="p.isKO"></div>
                      </div>
                   </div>
                </div>
             </div>

             <!-- Action Controls -->
             <div class="bg-gray-50 rounded-3xl p-6 border border-gray-100 shadow-sm relative">
                <div class="flex justify-between items-center mb-4">
                   <div>
                      <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Your Squad</span>
                      <p class="text-[8px] text-gray-400 font-bold uppercase mt-0.5">Select a pokemon to switch, or click "Rester" to keep current</p>
                   </div>
                   <button (click)="forfeit()" class="text-[10px] font-black text-red-500 uppercase tracking-widest hover:underline">Déclarer Forfait</button>
                </div>

                <div class="flex flex-wrap gap-4 justify-center">
                   <div *ngFor="let p of playerTeam" 
                        (click)="selectPokemon(p)"
                        class="w-20 h-20 bg-white rounded-2xl flex-shrink-0 flex flex-col items-center justify-center border-2 transition-all cursor-pointer p-2 shadow-sm relative group"
                        [class.border-poke-blue]="selectedPokemonToMove?.id === p.id"
                        [class.border-transparent]="selectedPokemonToMove?.id !== p.id"
                        [class.opacity-40]="p.isKO" [class.pointer-events-none]="p.isKO">
                      <img [src]="getSpriteUrl(p.id || p.pokemon_id)" class="w-12 h-12 object-contain group-hover:scale-110 transition-transform">
                      <div class="text-[8px] font-black uppercase tracking-tighter truncate w-full text-center mt-1">{{ p.name || p.pokemon_name }}</div>
                      <div *ngIf="activePokemon?.id === p.id || activePokemon?.pokemon_id === p.pokemon_id" class="absolute -top-2 -right-2 bg-poke-blue text-white text-[6px] font-black px-1.5 py-0.5 rounded-full uppercase">Active</div>
                   </div>
                </div>
                
                <div class="flex gap-4 mt-6">
                   <button 
                      [disabled]="!selectedPokemonToMove || turnProcessing"
                      (click)="playTurn('switch')"
                      class="flex-1 py-4 bg-gray-900 hover:bg-black text-white font-black rounded-2xl uppercase tracking-widest transition-all disabled:opacity-50">
                      {{ turnProcessing ? 'Resolving...' : 'Switch & Attack' }}
                   </button>
                   <button 
                      [disabled]="turnProcessing || !activePokemon"
                      (click)="playTurn('stay')"
                      class="px-8 py-4 bg-white border-2 border-gray-900 text-gray-900 font-black rounded-2xl uppercase tracking-widest hover:bg-gray-50 transition-all disabled:opacity-50">
                      Rester
                   </button>
                </div>
             </div>
          </div>

          <!-- PHASE: FINISHED -->
          <div *ngIf="phase === 'finished'" class="flex-1 bg-white rounded-3xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center animate-bounce-in">
             <div class="w-32 h-32 mb-6 relative">
                <div class="absolute inset-0 bg-yellow-400/20 rounded-full animate-ping"></div>
                <div class="relative w-full h-full bg-yellow-400 rounded-full flex items-center justify-center text-white shadow-xl">
                   <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-7.714 2.143L11 21l-2.286-6.857L1 12l7.714-2.143L11 3z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                </div>
             </div>
             <h2 class="text-4xl font-black text-gray-800 uppercase mb-2 tracking-tighter">
                {{ winner === 'red' ? 'Victory!' : (winner === 'blue' ? 'Defeat' : 'Draw') }}
             </h2>
             <p class="text-gray-500 mb-8 text-center">
                {{ winner === 'red' ? 'You crushed your opponent and earned 10 points!' : (winner === 'blue' ? 'Your opponent was stronger this time. You lost 10 points.' : 'An intense match ended in a draw.') }}
             </p>
             
             <div class="flex gap-4">
                <button (click)="reset()" class="px-10 py-4 bg-gray-900 text-white font-black rounded-2xl uppercase tracking-widest shadow-xl hover:scale-105 transition-all">Play Again</button>
                <button (click)="goHome()" class="px-10 py-4 bg-gray-100 text-gray-600 font-black rounded-2xl uppercase tracking-widest hover:bg-gray-200 transition-all">Dashboard</button>
             </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100%; background-color: #f8fafc; }
    .animate-fade-in { animation: fadeIn 0.5s ease-out; }
    .animate-slide-up { animation: slideUp 0.4s ease-out; }
    .animate-bounce-in { animation: bounceIn 0.8s cubic-bezier(0.36, 0, 0.66, -0.56) both; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes float { 
       0% { transform: translateY(0px); }
       50% { transform: translateY(-15px); }
       100% { transform: translateY(0px); }
    }
    @keyframes bounce-subtle {
       0%, 100% { transform: translateY(0); }
       50% { transform: translateY(-8px); }
    }
    @keyframes bounceIn {
       0% { transform: scale(0.3); opacity: 0; }
       50% { transform: scale(1.05); opacity: 1; }
       70% { transform: scale(0.9); }
       100% { transform: scale(1); }
    }
    .animate-float { animation: float 4s ease-in-out infinite; }
    .animate-bounce-subtle { animation: bounce-subtle 3s ease-in-out infinite; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
  `]
})
export class BattleArenaComponent implements OnInit, OnDestroy {
  @ViewChild('timer') timer!: BattleTimerComponent;

  currentUser: User | null = null;
  phase: BattlePhase = 'selection';
  selectedMode: BattleMode | null = null;
  myTeams: Team[] = [];
  selectedTeamId: string | null = null;

  // Battle State
  battle: Battle | null = null;
  playerTeam: any[] = [];
  opponentTeam: any[] = [];
  activePokemon: any = null;
  opponentActivePokemon: any = null;
  selectedPokemonToMove: any = null;
  scoreRed = 0;
  scoreBlue = 0;
  winner: string | null = null;

  // Draft State
  draftingPool: any[] = [];
  draftPicksRed: any[] = [];
  draftPicksBlue: any[] = [];
  isRedTurn = true;

  loading = false;
  turnProcessing = false;
  errorMessage: string | null = null;
  private subs = new Subscription();

  constructor(
    private authService: AuthService,
    private teamService: TeamService,
    private battleService: BattleService,
    private wsService: WebsocketService,
    private pokedexService: PokedexService
  ) {}

  ngOnInit() {
    this.authService.currentUser$.subscribe(user => this.currentUser = user);
    this.loadTeams();
  }

  ngOnDestroy() {
    this.subs.unsubscribe();
    this.wsService.disconnect();
  }

  loadTeams() {
    this.teamService.listTeams().subscribe(teams => {
      this.myTeams = teams;
    });
  }

  selectMode(mode: BattleMode) {
    this.selectedMode = mode;
  }

  async startMatchmaking() {
    if (!this.selectedMode) return;
    this.loading = true;
    this.errorMessage = null;

    console.log('BattleArena: Starting matchmaking for mode', this.selectedMode);

    // Map frontend modes to backend enum values
    const backendModeMap: any = {
      'constructed': 'construit',
      'random': 'hasard',
      'draft': 'pioche'
    };
    const mode = backendModeMap[this.selectedMode];

    this.battleService.getOpenBattles().subscribe({
      next: async (openBattles) => {
        console.log('BattleArena: Open battles found:', openBattles);
        const match = openBattles.find(b => b.mode === mode && b.player_red_id !== this.currentUser?.id);

        if (match) {
          console.log('BattleArena: Joining existing match:', match.id);
          this.wsService.connect('blue', this.currentUser?.username || 'Player');
          this.battleService.joinBattle(match.id, this.currentUser!.id).subscribe({
            next: async (battle) => {
              this.battle = battle;
              try {
                await this.initTeamsForMode();
                this.phase = 'battle';
                this.loading = false;
                this.startNewRound();
              } catch (err) {
                this.errorMessage = "Failed to initialize teams.";
                this.loading = false;
              }
            },
            error: (err) => {
              console.error('BattleArena: Join battle failed', err);
              this.errorMessage = "Failed to join battle. It might be full or closed.";
              this.loading = false;
            }
          });
        } else {
          console.log('BattleArena: No matching battle, creating new one');
          this.wsService.connect('red', this.currentUser?.username || 'Player');
          this.battleService.createBattle({
            player_red_id: this.currentUser!.id,
            player_blue_id: null as any,
            mode: mode
          }).subscribe({
            next: (battle) => {
              this.battle = battle;
              this.pollForOpponent(battle.id);
            },
            error: (err) => {
              console.error('BattleArena: Create battle failed', err);
              this.errorMessage = "Failed to create battle. Please try again.";
              this.loading = false;
            }
          });
        }
      },
      error: (err) => {
        console.error('BattleArena: Get open battles failed', err);
        this.errorMessage = "Connection error. Make sure the battle service is running.";
        this.loading = false;
      }
    });
  }

  pollForOpponent(battleId: string) {
    const pollInterval = setInterval(() => {
      this.battleService.getBattle(battleId).subscribe(battle => {
        if (battle.player_blue_id) {
          clearInterval(pollInterval);
          this.battle = battle;
          this.initTeamsForMode().then(() => {
            this.phase = 'battle';
            this.loading = false;
            this.startNewRound();
          });
        }
      });
    }, 2000);
    this.subs.add(() => clearInterval(pollInterval));
  }

  async initTeamsForMode() {
    if (this.selectedMode === 'draft') await this.initDraft();
    else if (this.selectedMode === 'random') await this.initRandom();
    else if (this.selectedMode === 'constructed') await this.initConstructed();
  }

  async initDraft() {
    this.loading = true;
    try {
      const pool = await firstValueFrom(this.pokedexService.getRandomPokemon(12));
      this.draftingPool = pool.map(p => ({ 
        ...p, 
        picked: false,
        types: p.types.map((t: any) => t.type.name) // Map to string array
      }));
      this.phase = 'drafting';
    } catch (err) {
      this.errorMessage = "Failed to load drafting pool.";
    }
    this.loading = false;
  }

  async initRandom() {
    const red = await firstValueFrom(this.pokedexService.getRandomPokemon(6));
    const blue = await firstValueFrom(this.pokedexService.getRandomPokemon(6));
    
    this.playerTeam = red.map(p => ({ 
      ...p, 
      isKO: false,
      types: p.types.map((t: any) => t.type.name)
    }));
    
    this.opponentTeam = blue.map(p => ({ 
      ...p, 
      isKO: false, 
      hasBeenSeen: false,
      types: p.types.map((t: any) => t.type.name)
    }));
    
    this.activePokemon = this.playerTeam[0];
    this.opponentActivePokemon = this.opponentTeam[0];
    this.opponentActivePokemon.hasBeenSeen = true;
  }

  async initConstructed() {
    const team = this.myTeams.find(t => t.id === this.selectedTeamId);
    if (team) {
      this.playerTeam = team.pokemon.map(p => ({ 
        id: p.pokemon_id, 
        name: p.pokemon_name, 
        types: [p.type1, ...(p.type2 ? [p.type2] : [])],
        isKO: false 
      }));
      const blue = await firstValueFrom(this.pokedexService.getRandomPokemon(6));
      this.opponentTeam = blue.map(p => ({ 
        ...p, 
        isKO: false, 
        hasBeenSeen: true,
        types: p.types.map((t: any) => t.type.name)
      }));
      this.activePokemon = this.playerTeam[0];
      this.opponentActivePokemon = this.opponentTeam[0];
    }
  }

  pickPokemon(p: any) {
    if (p.picked) return;
    
    p.picked = true;
    if (this.isRedTurn) {
      this.draftPicksRed.push(p);
      this.playerTeam.push({ ...p, isKO: false });
      this.isRedTurn = false;
    } else {
      this.draftPicksBlue.push(p);
      this.opponentTeam.push({ ...p, isKO: false, hasBeenSeen: true });
      this.isRedTurn = true;
    }

    if (this.draftingPool.every(pk => pk.picked)) {
      this.activePokemon = this.playerTeam[0];
      this.opponentActivePokemon = this.opponentTeam[0];
      this.opponentActivePokemon.hasBeenSeen = true;
      this.phase = 'battle';
      this.startNewRound();
    }
  }

  selectPokemon(p: any) {
    if (this.turnProcessing || p.isKO) return;
    this.selectedPokemonToMove = p;
  }

  playTurn(type: 'switch' | 'stay') {
    if (!this.battle || this.turnProcessing) return;
    
    if (type === 'switch' && !this.selectedPokemonToMove) return;
    
    const nextPokemon = type === 'switch' ? this.selectedPokemonToMove : this.activePokemon;
    this.turnProcessing = true;
    
    this.battleService.playTurn(this.battle.id, {
      pokemon_red: nextPokemon.name || nextPokemon.pokemon_name,
      pokemon_blue: this.opponentActivePokemon.name,
      types_red: nextPokemon.types || [nextPokemon.type1, nextPokemon.type2].filter(t => t),
      types_blue: this.opponentActivePokemon.types
    }).subscribe({
      next: (result) => {
        this.processTurnResult(result, nextPokemon);
      },
      error: () => {
        this.turnProcessing = false;
      }
    });
  }

  processTurnResult(result: any, nextPokemon: any) {
    this.activePokemon = nextPokemon;
    this.selectedPokemonToMove = null;
    this.turnProcessing = false;
    
    if (result.result === 'A') {
      this.scoreRed++;
      this.opponentActivePokemon.isKO = true;
      this.logToBot(`Turn ${this.battle?.current_turn}: ${this.activePokemon.name || this.activePokemon.pokemon_name} defeated ${this.opponentActivePokemon.name}!`);
      const nextOpponent = this.opponentTeam.find(p => !p.isKO);
      if (nextOpponent) {
        this.opponentActivePokemon = nextOpponent;
        this.opponentActivePokemon.hasBeenSeen = true;
      } else {
        this.endBattle('red');
      }
    } else if (result.result === 'B') {
      this.scoreBlue++;
      this.activePokemon.isKO = true;
      this.logToBot(`Turn ${this.battle?.current_turn}: ${this.opponentActivePokemon.name} defeated ${this.activePokemon.name || this.activePokemon.pokemon_name}!`);
      const nextPlayer = this.playerTeam.find(p => !p.isKO);
      if (nextPlayer) {
        this.activePokemon = nextPlayer;
      } else {
        this.endBattle('blue');
      }
    } else {
      this.logToBot(`Turn ${this.battle?.current_turn}: It's a draw between both Pokémon!`);
      this.activePokemon.isKO = true;
      this.opponentActivePokemon.isKO = true;
      const nextP = this.playerTeam.find(p => !p.isKO);
      const nextO = this.opponentTeam.find(p => !p.isKO);
      if (nextP) this.activePokemon = nextP;
      if (nextO) {
        this.opponentActivePokemon = nextO;
        this.opponentActivePokemon.hasBeenSeen = true;
      }
      
      if (!nextP && !nextO) this.endBattle('draw');
      else if (!nextP) this.endBattle('blue');
      else if (!nextO) this.endBattle('red');
    }
    
    if (this.phase === 'battle') {
      this.startNewRound();
    }
  }

  startNewRound() {
    if (this.timer) {
      this.timer.reset();
    }
  }

  onTimeout() {
    this.logToBot('Time is up! You forfeited the turn.');
    this.endBattle('blue');
  }

  forfeit() {
    this.endBattle('blue');
    this.logToBot('You have forfeited the match.');
  }

  endBattle(winner: string) {
    this.winner = winner;
    this.phase = 'finished';
    this.timer?.stopTimer();
    this.logToBot(`Match finished. Winner: ${winner === 'red' ? 'YOU' : (winner === 'blue' ? 'OPPONENT' : 'DRAW')}`);
  }

  logToBot(content: string) {
    this.wsService.sendMessage(`[BOT] ${content}`);
  }

  getTypeColor(type: string): string {
    const colors: any = {
      // French
      'Normal': '#A8A878', 'Feu': '#F08030', 'Eau': '#6890F0', 'Plante': '#78C850',
      'Electrik': '#F8D030', 'Glace': '#98D8D8', 'Combat': '#C03028', 'Poison': '#A040A0',
      'Sol': '#E0C068', 'Vol': '#A890F0', 'Psy': '#F85888', 'Insecte': '#A8B820',
      'Roche': '#B8A038', 'Spectre': '#705898', 'Dragon': '#7038F8', 'Tenebres': '#705848',
      'Acier': '#B8B8D0', 'Fee': '#EE99AC',
      // English (PokeAPI)
      'normal': '#A8A878', 'fire': '#F08030', 'water': '#6890F0', 'grass': '#78C850',
      'electric': '#F8D030', 'ice': '#98D8D8', 'fighting': '#C03028', 'poison': '#A040A0',
      'ground': '#E0C068', 'flying': '#A890F0', 'psychic': '#F85888', 'bug': '#A8B820',
      'rock': '#B8A038', 'ghost': '#705898', 'dragon': '#7038F8', 'dark': '#705848',
      'steel': '#B8B8D0', 'fairy': '#EE99AC'
    };
    return colors[type] || colors[type.toLowerCase()] || '#777';
  }

  getSpriteUrl(pokemonId: number | string): string {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemonId}.png`;
  }

  reset() {
    this.phase = 'selection';
    this.selectedMode = null;
    this.battle = null;
    this.playerTeam = [];
    this.opponentTeam = [];
    this.activePokemon = null;
    this.opponentActivePokemon = null;
    this.scoreRed = 0;
    this.scoreBlue = 0;
    this.winner = null;
    this.draftingPool = [];
    this.draftPicksRed = [];
    this.draftPicksBlue = [];
    this.isRedTurn = true;
  }

  goHome() {
    window.location.href = '/dashboard';
  }
}
