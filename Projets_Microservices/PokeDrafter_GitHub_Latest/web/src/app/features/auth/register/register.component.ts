import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { InputComponent } from '../../../shared/components/input/input.component';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, CardComponent, InputComponent],
  template: `
    <div class="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      
      <div class="mb-6 flex flex-col items-center">
        <img src="assets/logo.png" alt="Logo" class="h-24 object-contain mb-4">
        <h2 class="text-xl font-bold text-gray-800">Join the squad!</h2>
      </div>

      <div class="w-full max-w-sm space-y-6">
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
               <app-input label="Firstname" placeholder="Jean" [(ngModel)]="form.first_name" name="first_name" class="light-theme-input"></app-input>
               <app-input label="Lastname" placeholder="Doe" [(ngModel)]="form.last_name" name="last_name" class="light-theme-input"></app-input>
            </div>
            
            <app-input label="Mail" placeholder="jeandoe@gmail.com" type="email" [(ngModel)]="form.email" name="email" class="light-theme-input"></app-input>
            <app-input label="Username" placeholder="jeandoe" [(ngModel)]="form.username" name="username" class="light-theme-input"></app-input>
            <app-input label="Password" placeholder="•••••" type="password" [(ngModel)]="form.password" name="password" class="light-theme-input"></app-input>
  
            <div class="pt-2 flex items-center justify-between px-2">
              <label class="text-sm font-medium text-gray-700">Team</label>
              <div class="flex gap-4">
                <button 
                  type="button" 
                  (click)="form.color = 'RED'"
                  class="w-8 h-8 rounded-full transition-transform hover:scale-110 focus:outline-none shadow-sm relative"
                  [style.background-color]="'#FF0000'"
                  title="Red Team"
                >
                  <div *ngIf="form.color === 'RED'" class="absolute inset-0 rounded-full border-2 border-black"></div>
                </button>
                <button 
                  type="button" 
                  (click)="form.color = 'BLUE'"
                  class="w-8 h-8 rounded-full transition-transform hover:scale-110 focus:outline-none shadow-sm relative"
                  [style.background-color]="'#0558b1'"
                  title="Blue Team"
                >
                  <div *ngIf="form.color === 'BLUE'" class="absolute inset-0 rounded-full border-2 border-black"></div>
                </button>
              </div>
            </div>
          </div>

        <div *ngIf="errorMessage" class="text-red-500 text-sm text-center font-medium">
          {{ errorMessage }}
        </div>

        <div class="space-y-3 pt-4">
          <button 
            type="submit" 
            class="w-full py-3 bg-poke-blue hover:bg-poke-blue-dark text-white font-bold rounded-full shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50"
            [disabled]="loading"
            (click)="register()">
            {{ loading ? 'CREATING ACCOUNT...' : 'SIGN UP' }}
          </button>
          
          <button 
            type="button" 
            class="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-full shadow-sm transform hover:scale-105 transition-all duration-200"
            (click)="goToLogin()">
            RETURN
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
      padding-left: 1.5rem !important;
    }
    :host ::ng-deep .light-theme-input label {
        color: #374151 !important;
        margin-left: 0.5rem;
    }
  `]
})
export class RegisterComponent {
  form = {
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    password: '',
    color: 'RED' as 'RED' | 'BLUE'
  };
  loading = false;
  errorMessage = '';

  constructor(private router: Router, private authService: AuthService) { }

  register() {
    this.loading = true;
    this.errorMessage = '';
    this.authService.register(this.form).subscribe({
      next: () => {
        // Automatically login after successful registration
        this.authService.login({ 
          username_or_email: this.form.email, 
          password: this.form.password 
        }).subscribe({
          next: () => {
            this.loading = false;
            this.router.navigate(['/dashboard']);
          },
          error: (err: any) => {
             this.loading = false;
             this.router.navigate(['/auth/login']);
          }
        });
      },
      error: (err: any) => {
        this.loading = false;
        if (err.error?.detail && Array.isArray(err.error.detail)) {
            this.errorMessage = err.error.detail.map((e: any) => `${e.loc[e.loc.length-1]}: ${e.msg}`).join(', ');
        } else {
            this.errorMessage = err.error?.detail || 'Registration failed. Please check your inputs.';
        }
        console.error('Register error', err);
      }
    });
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }
}
