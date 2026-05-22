import { TestBed } from '@angular/core/testing';
import { TeamManagerComponent } from './team-manager.component';

describe('TeamManagerComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TeamManagerComponent]
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(TeamManagerComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should initialize with empty teams', () => {
    const fixture = TestBed.createComponent(TeamManagerComponent);
    const component = fixture.componentInstance;
    expect(component.teams).toEqual([]);
  });

  it('should toggle create form', () => {
    const fixture = TestBed.createComponent(TeamManagerComponent);
    const component = fixture.componentInstance;
    
    expect(component.show_create_form).toBe(false);
    component.show_create_form = true;
    expect(component.show_create_form).toBe(true);
  });
});
