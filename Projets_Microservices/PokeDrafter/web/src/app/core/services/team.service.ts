import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface TeamPokemon {
  pokemon_id: number;
  pokemon_name: string;
  type1: string;
  type2?: string;
  slot: number;
}

export interface Team {
  id: string;
  name: string;
  pokemon: TeamPokemon[];
  created_at: string;
  updated_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class TeamService {
  private apiUrl = `${environment.apiUrl}/teams/`;

  constructor(private http: HttpClient) { }

  listTeams(): Observable<Team[]> {
    return this.http.get<Team[]>(this.apiUrl);
  }

  createTeam(payload: { name: string, pokemon: TeamPokemon[] }): Observable<Team> {
    return this.http.post<Team>(this.apiUrl, payload);
  }

  getTeam(id: string): Observable<Team> {
    return this.http.get<Team>(`${this.apiUrl}${id}`);
  }

  updateTeam(id: string, payload: { name?: string, pokemon?: TeamPokemon[] }): Observable<Team> {
    return this.http.put<Team>(`${this.apiUrl}${id}`, payload);
  }

  deleteTeam(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}`);
  }
}
