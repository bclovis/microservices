import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { InputComponent } from '../../../shared/components/input/input.component';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, CardComponent, InputComponent],
  template: `
    <div class="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      
      <div class="mb-6 flex flex-col items-center">
        <img src="assets/logo.png" alt="Logo" class="h-24 object-contain mb-4">
        <h2 class="text-xl font-bold text-gray-800">Welcome to the game!</h2>
      </div>

      <div class="w-full max-w-sm space-y-6">
        <div class="space-y-4">
          <app-input 
            label="Email or Username" 
            placeholder="jeandoe or jeandoe@gmail.com" 
            [(ngModel)]="credentials.username_or_email" 
            name="username_or_email"
            class="light-theme-input"
          ></app-input>
          
          <div class="space-y-1">
            <app-input 
              label="Password" 
              type="password" 
              placeholder="••••••••" 
              [(ngModel)]="credentials.password" 
              name="password"
              class="light-theme-input"
            ></app-input>
          </div>
        </div>

        <div *ngIf="errorMessage" class="text-red-500 text-sm text-center font-medium">
          {{ errorMessage }}
        </div>

        <div class="space-y-3 pt-2">
          <button 
            type="submit" 
            class="w-full py-3 bg-poke-blue hover:bg-poke-blue-dark text-white font-bold rounded-full shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50"
            [disabled]="loading"
            (click)="login()">
            {{ loading ? 'LOGGING IN...' : 'LOGIN' }}
          </button>
          
          <button 
            type="button" 
            class="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-full shadow-sm transform hover:scale-105 transition-all duration-200"
            (click)="goToRegister()">
            SIGN UP
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host ::ng-deep .light-theme-input input {
      background-color: #F3F4F6 !important;
      border: 1px solid #E5E7EB !important;
      color: #1F2937 !important;
      border-radius: 9999px !important;
    }
    :host ::ng-deep .light-theme-input label {
        color: #374151 !important;
        margin-left: 0.5rem;
    }
  `]
})
export class LoginComponent {
  credentials = {
    username_or_email: '',
    password: ''
  };
  loading = false;
  errorMessage = '';

  constructor(private router: Router, private authService: AuthService) { }

  login() {
    this.loading = true;
    this.errorMessage = '';
    this.authService.login(this.credentials).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        this.loading = false;
        if (err.error?.detail && Array.isArray(err.error.detail)) {
            this.errorMessage = err.error.detail.map((e: any) => `${e.loc[e.loc.length-1]}: ${e.msg}`).join(', ');
        } else {
            this.errorMessage = err.error?.detail || 'Login failed. Please check your credentials.';
        }
        console.error('Login error', err);
      }
    });
  }

  goToRegister() {
    this.router.navigate(['/auth/register']);
  }
}
