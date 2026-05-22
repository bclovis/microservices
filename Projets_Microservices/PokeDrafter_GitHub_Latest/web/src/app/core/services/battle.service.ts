import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface BattleCreate {
  player_red_id: string;
  player_blue_id: string;
  mode: string;
}

export interface BattleJoin {
  player_blue_id: string;
}

export interface Battle {
  id: string;
  player_red_id: string;
  player_blue_id: string;
  status: string;
  current_turn: number;
  mode: string;
  winner?: string;
}

export interface TurnPlay {
  pokemon_red: string;
  pokemon_blue: string;
  types_red: string[];
  types_blue: string[];
}

@Injectable({
  providedIn: 'root'
})
export class BattleService {
  private apiUrl = `${environment.apiUrl}/battle/battles/`;

  constructor(private http: HttpClient) { }

  createBattle(payload: BattleCreate): Observable<Battle> {
    return this.http.post<Battle>(`${this.apiUrl}`, payload);
  }

  getOpenBattles(): Observable<Battle[]> {
    return this.http.get<Battle[]>(`${this.apiUrl}open`);
  }

  joinBattle(battleId: string, playerBlueId: string): Observable<Battle> {
    return this.http.post<Battle>(`${this.apiUrl}${battleId}/join`, { player_blue_id: playerBlueId });
  }

  playTurn(battleId: string, payload: TurnPlay): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}${battleId}/turn`, payload);
  }

  getBattle(battleId: string): Observable<Battle> {
    return this.http.get<Battle>(`${this.apiUrl}${battleId}`);
  }

  getHistory(userId: string): Observable<Battle[]> {
    return this.http.get<Battle[]> (`${this.apiUrl}history/${userId}`);
  }
}
