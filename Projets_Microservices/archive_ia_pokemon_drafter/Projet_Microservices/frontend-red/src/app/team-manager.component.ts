import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface Pokemon {
  id: number;
  name: string;
  type_primary: string;
  type_secondary?: string;
}

interface Team {
  id?: number;
  name: string;
  pokemon_ids: number[];
}

@Component({
  selector: 'app-team-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="team-manager">
      <h2>My Teams</h2>
      
      <button (click)="show_create_form = true" class="btn-primary">
        Create New Team
      </button>
      
      <div *ngIf="show_create_form" class="create-form">
        <input [(ngModel)]="new_team_name" placeholder="Team Name" />
        <button (click)="createTeam()">Create</button>
        <button (click)="show_create_form = false">Cancel</button>
      </div>
      
      <div class="teams-list">
        <div *ngFor="let team of teams" class="team-card">
          <h3>{{ team.name }}</h3>
          <p>Pokemon: {{ team.pokemon_ids.length }}/6</p>
          <div class="team-actions">
            <button (click)="editTeam(team)">Modify</button>
            <button (click)="deleteTeam(team)">Delete</button>
            <button (click)="completeTeam(team)">Complete</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .team-manager {
      padding: 2rem;
      color: white;
    }
    
    .team-card {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 1rem;
      margin: 1rem 0;
    }
    
    .btn-primary {
      background: #ff6b6b;
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .btn-primary:hover {
      background: #ff5252;
    }
  `]
})
export class TeamManagerComponent implements OnInit {
  teams: Team[] = [];
  show_create_form = false;
  new_team_name = '';
  
  ngOnInit() {
    this.loadTeams();
  }
  
  loadTeams() {
    // TODO: Call API to load teams
    console.log('Loading teams...');
  }
  
  createTeam() {
    const team: Team = {
      name: this.new_team_name,
      pokemon_ids: []
    };
    
    // TODO: Call API to create team
    console.log('Creating team:', team);
    this.show_create_form = false;
    this.new_team_name = '';
  }
  
  editTeam(team: Team) {
    // TODO: Navigate to edit view
    console.log('Editing team:', team);
  }
  
  deleteTeam(team: Team) {
    if (confirm(`Delete team "${team.name}"?`)) {
      // TODO: Call API to delete team
      console.log('Deleting team:', team);
    }
  }
  
  completeTeam(team: Team) {
    // TODO: Call recommendation API
    console.log('Getting recommendations for:', team);
  }
}
