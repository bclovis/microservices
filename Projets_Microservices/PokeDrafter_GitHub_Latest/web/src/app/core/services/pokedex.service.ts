import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface PokeApiListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: { name: string; url: string }[];
}

@Injectable({
  providedIn: 'root'
})
export class PokedexService {
  private apiUrl = `${environment.apiUrl}/pokedex/`;

  constructor(private http: HttpClient) { }

  getPokemonList(offset: number = 0, limit: number = 20): Observable<PokeApiListResponse> {
    const params = new HttpParams()
      .set('offset', offset.toString())
      .set('limit', limit.toString());
    
    return this.http.get<PokeApiListResponse>(this.apiUrl, { params });
  }

  getPokemonDetail(name: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}${name}`);
  }

  searchPokemon(name: string): Observable<{ name: string; url: string }[]> {
    const params = new HttpParams().set('name', name);
    return this.http.get<{ name: string; url: string }[]>(`${this.apiUrl}search`, { params });
  }

  getRandomPokemon(count: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}random/${count}`);
  }
}
